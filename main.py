import asyncio
import json
import os
import math
from telethon import TelegramClient, sessions # 1. Importa 'sessions'
from telethon.tl.types import InputMessagesFilterVideo
from fastapi import FastAPI, HTTPException, Request, Header, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

# === CONFIGURAÇÃO DE PERFIL (Sua lógica está perfeita) ===
PERFIL_ATIVO = "rapido" # Sugestão: 'rapido' é mais estável que 'ultra_rapido' no Render
PERFIS = {
    "ultra_rapido": { "CHUNK_SIZE": 1024 * 1024, "MIN_BUFFER": 512 * 1024, "RANGE_CHUNK": 50 * 1024 * 1024, "PREFETCH_CHUNKS": 3 },
    "rapido": { "CHUNK_SIZE": 512 * 1024, "MIN_BUFFER": 256 * 1024, "RANGE_CHUNK": 20 * 1024 * 1024, "PREFETCH_CHUNKS": 2 },
    "medio": { "CHUNK_SIZE": 256 * 1024, "MIN_BUFFER": 128 * 1024, "RANGE_CHUNK": 10 * 1024 * 1024, "PREFETCH_CHUNKS": 1 },
    "economico": { "CHUNK_SIZE": 128 * 1024, "MIN_BUFFER": 64 * 1024, "RANGE_CHUNK": 5 * 1024 * 1024, "PREFETCH_CHUNKS": 0 }
}
config = PERFIS[PERFIL_ATIVO]
CHUNK_SIZE = config["CHUNK_SIZE"]
MIN_BUFFER = config["MIN_BUFFER"]
RANGE_CHUNK = config["RANGE_CHUNK"]
PREFETCH_CHUNKS = config["PREFETCH_CHUNKS"]
print(f"🎯 Perfil: {PERFIL_ATIVO.upper()}")

# === 2. CORREÇÃO: Lendo do Ambiente do Render ===
API_ID = int(os.environ.get("API_ID", 0))
API_HASH = os.environ.get("API_HASH", "")
GRUPO_ALVO = int(os.environ.get("GRUPO_ALVO", 0))
SESSION_STRING = os.environ.get("TELEGRAM_SESSION_STRING", None)

# --- CORREÇÃO IMPORTANTE ---
# Removemos a lógica do 'DATA_PATH'.
# O script agora espera o mapa na *mesma pasta* que o main.py
MAPA_PATH = 'mapeamento_aulas.json' 
# --- FIM DA CORREÇÃO ---

app = FastAPI()

# === 3. CORREÇÃO: Adicione a URL do seu Vercel aqui ===
origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "https://SEU-SITE-DO-VERCEL.vercel.app", # <-- MUDE AQUI
    "*" # Mantenha para testes
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === 4. CORREÇÃO: Login com SESSION_STRING (Não interativo) ===
if not SESSION_STRING:
    print("❌ ERRO CRÍTICO: TELEGRAM_SESSION_STRING não definida no ambiente!")
    client = TelegramClient('local_session_fail', API_ID, API_HASH) # Vai falhar no Render (o que é bom)
else:
    print("... Usando SESSION_STRING para login ...")
    client = TelegramClient(sessions.StringSession(SESSION_STRING), API_ID, API_HASH)

# === CACHES (sem mudança) ===
mapeamento_cache = None
mensagens_cache = {}
chunk_cache = {} 

# === 5. CORREÇÃO: 'carregar_mapeamento' usa MAPA_PATH local ===
def carregar_mapeamento():
    global mapeamento_cache
    if mapeamento_cache is None:
        if os.path.exists(MAPA_PATH): # <-- LÊ O ARQUIVO LOCAL
            with open(MAPA_PATH, 'r', encoding='utf-8') as f:
                mapeamento_cache = json.load(f)
                print(f"✅ Mapeamento: {len(mapeamento_cache)} aulas (de {MAPA_PATH})")
        else:
            print(f"⚠️ Arquivo {MAPA_PATH} não encontrado!")
            mapeamento_cache = {}
    return mapeamento_cache

# === 6. CORREÇÃO: 'startup_event' não usa client.start() ===
@app.on_event("startup")
async def startup_event():
    print("Iniciando servidor e conectando ao Telegram...")
    await client.connect() # Apenas conecta (já está logado via String)
    print("✅ Telegram conectado!")
    carregar_mapeamento()

@app.on_event("shutdown")
async def shutdown_event():
    await client.disconnect()

# --- O resto do seu código (get_message_cached, prefetch_chunks, stream_generator_with_prefetch, 
# full_stream_generator, stream_por_codigo, stream_por_id, get_mapeamento, etc.)
# pode continuar EXATAMENTE IGUAL ao que você me mandou no [Prompt 207].
# A lógica de 'seek' e 'prefetch' estava correta.
async def get_message_cached(message_id: int):
    if message_id in mensagens_cache:
        return mensagens_cache[message_id]
    entity = await client.get_entity(GRUPO_ALVO)
    message = await client.get_messages(entity, ids=message_id)
    if not message or not message.video:
        raise HTTPException(404, detail="Vídeo não encontrado")
    mensagens_cache[message_id] = message
    return message
async def prefetch_chunks(message, start_offset: int, message_id: int):
    if PREFETCH_CHUNKS == 0: return
    try:
        offsets = [start_offset + (RANGE_CHUNK * i) for i in range(1, PREFETCH_CHUNKS + 1)]
        for offset in offsets:
            if offset >= message.video.size: break
            cache_key = (message_id, offset)
            if cache_key in chunk_cache: continue
            end_offset = min(offset + RANGE_CHUNK - 1, message.video.size - 1)
            chunk_data = bytearray()
            print(f"🔮 Prefetch: {offset}-{end_offset} ({(end_offset - offset) / (1024*1024):.1f} MB)")
            async for chunk in client.iter_download(
                message.media, offset=offset, request_size=CHUNK_SIZE,
                file_size=message.video.size, limit=(end_offset - offset + 1)
            ):
                chunk_data.extend(chunk)
                if len(chunk_data) >= (end_offset - offset + 1): break
            chunk_cache[cache_key] = bytes(chunk_data)
            print(f"💾 Chunk {offset} cacheado!")
    except Exception as e:
        print(f"⚠️ Erro no prefetch: {e}")
async def stream_generator_with_prefetch(message, start_byte: int, end_byte: int, message_id: int, background_tasks: BackgroundTasks):
    bytes_para_enviar = (end_byte - start_byte) + 1
    cache_key = (message_id, start_byte)
    if cache_key in chunk_cache:
        print(f"⚡ CACHE HIT! Chunk {start_byte} já estava pronto!")
        yield chunk_cache[cache_key][:bytes_para_enviar]
        del chunk_cache[cache_key] 
        background_tasks.add_task(prefetch_chunks, message, end_byte + 1, message_id)
        return
    print(f"📥 Baixando: {start_byte}-{end_byte}")
    bytes_enviados = 0
    buffer = bytearray()
    try:
        async for chunk in client.iter_download(
            message.media, offset=start_byte, request_size=CHUNK_SIZE, file_size=message.video.size
        ):
            buffer.extend(chunk)
            if bytes_enviados + len(buffer) >= bytes_para_enviar:
                bytes_restantes = bytes_para_enviar - bytes_enviados
                yield bytes(buffer[:bytes_restantes])
                break
            if len(buffer) >= MIN_BUFFER:
                yield bytes(buffer)
                bytes_enviados += len(buffer)
                buffer.clear()
        if buffer and bytes_enviados < bytes_para_enviar:
            yield bytes(buffer)
        background_tasks.add_task(prefetch_chunks, message, end_byte + 1, message_id)
    except asyncio.CancelledError: pass
    except Exception as e: print(f"❌ Erro: {e}")
async def full_stream_generator(message):
    buffer = bytearray()
    try:
        async for chunk in client.iter_download(
            message.media, request_size=CHUNK_SIZE, file_size=message.video.size
        ):
            buffer.extend(chunk)
            if len(buffer) >= MIN_BUFFER:
                yield bytes(buffer)
                buffer.clear()
        if buffer:
            yield bytes(buffer)
    except asyncio.CancelledError: pass
    except Exception as e: print(f"❌ Erro: {e}")
@app.get("/stream/code/{codigo}")
async def stream_por_codigo(
    codigo: str,
    range: Optional[str] = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if not codigo.startswith('#'):
        codigo = f"#{codigo.upper()}"
    else:
        codigo = codigo.upper()
    mapeamento = carregar_mapeamento()
    if codigo not in mapeamento:
        raise HTTPException(404, detail=f"Aula {codigo} não encontrada")
    message_id = mapeamento[codigo]["message_id"]
    return await stream_por_id(message_id, range, background_tasks)
async def stream_por_id(
    message_id: int, 
    range: Optional[str] = None,
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    try:
        message = await get_message_cached(message_id)
        video_size = message.video.size
        if range:
            bytes_unit, range_str = range.split("=")
            if bytes_unit != "bytes":
                raise HTTPException(416, detail="Range Not Satisfiable")
            parts = range_str.split("-")
            start_byte = int(parts[0]) if parts[0] else 0
            if len(parts) > 1 and parts[1]:
                end_byte = min(int(parts[1]), video_size - 1)
            else:
                # CORREÇÃO DO 'SEEK' (O BUG DO TRAVAMENTO)
                end_byte = min(start_byte + RANGE_CHUNK - 1, video_size - 1)
            content_length = (end_byte - start_byte) + 1
            print(f"📹 ID {message_id}: {start_byte}-{end_byte} ({content_length / (1024*1024):.1f} MB)")
            headers = {
                'Content-Range': f'bytes {start_byte}-{end_byte}/{video_size}',
                'Content-Length': str(content_length),
                'Accept-Ranges': 'bytes',
                'Content-Type': 'video/mp4',
                'Cache-Control': 'public, max-age=3600',
            }
            return StreamingResponse(
                stream_generator_with_prefetch(message, start_byte, end_byte, message_id, background_tasks),
                status_code=206,
                headers=headers,
                media_type="video/mp4"
            )
        else:
            headers = {
                'Content-Length': str(video_size),
                'Accept-Ranges': 'bytes',
                'Content-Type': 'video/mp4',
                'Cache-Control': 'public, max-age=3600',
            }
            return StreamingResponse(
                full_stream_generator(message),
                status_code=200,
                headers=headers,
                media_type="video/mp4"
            )
    except HTTPException:
        raise
    except Exception as e:
        print(f"❌ Erro: {e}")
        raise HTTPException(500, detail=f"Erro: {e}")
@app.get("/mapeamento")
async def get_mapeamento():
    mapeamento = carregar_mapeamento()
    if not mapeamento:
        raise HTTPException(404, detail="Mapeamento não encontrado")
    return JSONResponse(content={"total": len(mapeamento), "aulas": mapeamento})
@app.get("/listar-videos")
async def listar_videos():
    try:
        entity = await client.get_entity(GRUPO_ALVO)
        videos = []
        async for msg in client.iter_messages(entity, limit=100, filter=InputMessagesFilterVideo):
            if msg and msg.video:
                titulo = msg.message if msg.message else msg.file.name if msg.file else "Sem título"
                videos.append({ "id": msg.id, "titulo": titulo, "tamanho_mb": round(msg.video.size / (1024*1024), 2), "duracao_segundos": msg.video.duration })
        return JSONResponse(content={"total": len(videos), "videos": videos})
    except Exception as e:
        raise HTTPException(500, detail=f"Erro: {e}")
@app.get("/health")
async def health_check():
    return JSONResponse(content={
        "status": "ok", "perfil": PERFIL_ATIVO, "prefetch_chunks": PREFETCH_CHUNKS,
        "telegram_connected": client.is_connected(), "mapeamento_loaded": len(carregar_mapeamento()) > 0,
        "cache_mensagens": len(mensagens_cache), "cache_chunks": len(chunk_cache)
    })
@app.post("/limpar-cache")
async def limpar_cache():
    global mensagens_cache, mapeamento_cache, chunk_cache
    mensagens_cache.clear()
    chunk_cache.clear()
    mapeamento_cache = None
    carregar_mapeamento()
    return { "status": "Cache limpo!", "perfil": PERFIL_ATIVO, "prefetch": f"{PREFETCH_CHUNKS} chunks" }