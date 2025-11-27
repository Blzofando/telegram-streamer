import asyncio
import json
import os
from telethon import TelegramClient
from telethon.sessions import StringSession
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional
from dotenv import load_dotenv

load_dotenv()

# === CONFIGURAÇÃO DE PERFIL DE STREAMING ===
PERFIL_ATIVO = "rapido" # Ajuste conforme necessário

PERFIS = {
    "ultra_rapido": {"CHUNK_SIZE": 1024 * 1024, "MIN_BUFFER": 512 * 1024, "RANGE_CHUNK": 50 * 1024 * 1024, "PREFETCH": 3},
    "rapido":       {"CHUNK_SIZE": 512 * 1024,  "MIN_BUFFER": 256 * 1024, "RANGE_CHUNK": 20 * 1024 * 1024, "PREFETCH": 2},
    "medio":        {"CHUNK_SIZE": 256 * 1024,  "MIN_BUFFER": 128 * 1024, "RANGE_CHUNK": 10 * 1024 * 1024, "PREFETCH": 1},
}
config = PERFIS[PERFIL_ATIVO]
CHUNK_SIZE = config["CHUNK_SIZE"]
MIN_BUFFER = config["MIN_BUFFER"]
RANGE_CHUNK = config["RANGE_CHUNK"]
PREFETCH_CHUNKS = config["PREFETCH"]

# === CONFIGURAÇÃO TELEGRAM ===
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
SESSION_STRING = os.environ['TELEGRAM_SESSION_STRING']

app = FastAPI()

# CORS
origins = ["*"] # Em produção, especifique seus domínios
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

client = TelegramClient(StringSession(SESSION_STRING), API_ID, API_HASH)

# === CACHES ===
mapeamento_cache = None
# Cache de mensagens: Chave agora é (channel_id, message_id)
mensagens_cache = {} 
# Cache de chunks: Chave é (channel_id, message_id, offset)
chunk_cache = {} 

def carregar_mapeamento():
    global mapeamento_cache
    if mapeamento_cache is None:
        if os.path.exists('mapeamento_aulas.json'):
            with open('mapeamento_aulas.json', 'r', encoding='utf-8') as f:
                mapeamento_cache = json.load(f)
                print(f"✅ Mapeamento carregado: {len(mapeamento_cache)} aulas")
        else:
            mapeamento_cache = {}
            print("⚠️ mapeamento_aulas.json não encontrado!")
    return mapeamento_cache

@app.on_event("startup")
async def startup_event():
    await client.start()
    print("✅ Telegram conectado!")
    carregar_mapeamento()

@app.on_event("shutdown")
async def shutdown_event():
    await client.disconnect()

async def get_message_cached(channel_id: int, message_id: int):
    """Busca mensagem com cache, usando ID do canal e da mensagem"""
    cache_key = (channel_id, message_id)
    
    if cache_key in mensagens_cache:
        return mensagens_cache[cache_key]
    
    try:
        # Pega a entidade do canal (cacheado internamente pelo Telethon)
        entity = await client.get_entity(channel_id)
        message = await client.get_messages(entity, ids=message_id)
        
        if not message or not message.video:
            raise HTTPException(404, detail=f"Vídeo não encontrado no canal {channel_id}")
        
        mensagens_cache[cache_key] = message
        return message
    except Exception as e:
        print(f"Erro ao buscar mensagem: {e}")
        raise HTTPException(404, detail="Mensagem ou canal não encontrado")

# === STREAMING CORE ===

async def prefetch_chunks(message, start_offset: int, channel_id: int, message_id: int):
    if PREFETCH_CHUNKS == 0: return
    
    try:
        offsets = [start_offset + (RANGE_CHUNK * i) for i in range(1, PREFETCH_CHUNKS + 1)]
        for offset in offsets:
            if offset >= message.video.size: break
            
            cache_key = (channel_id, message_id, offset)
            if cache_key in chunk_cache: continue
            
            end_offset = min(offset + RANGE_CHUNK - 1, message.video.size - 1)
            chunk_data = bytearray()
            
            # print(f"🔮 Prefetch: {offset}")
            async for chunk in client.iter_download(
                message.media, offset=offset, request_size=CHUNK_SIZE,
                file_size=message.video.size, limit=(end_offset - offset + 1)
            ):
                chunk_data.extend(chunk)
                if len(chunk_data) >= (end_offset - offset + 1): break
            
            chunk_cache[cache_key] = bytes(chunk_data)
            
    except Exception as e:
        print(f"⚠️ Erro prefetch: {e}")

async def stream_generator(message, start_byte: int, end_byte: int, channel_id: int, message_id: int, background_tasks: BackgroundTasks):
    bytes_para_enviar = (end_byte - start_byte) + 1
    cache_key = (channel_id, message_id, start_byte)
    
    # 1. Tenta pegar do Cache (Prefetch)
    if cache_key in chunk_cache:
        # print(f"⚡ Cache Hit: {start_byte}")
        yield chunk_cache[cache_key][:bytes_para_enviar]
        del chunk_cache[cache_key]
        background_tasks.add_task(prefetch_chunks, message, end_byte + 1, channel_id, message_id)
        return

    # 2. Se não, baixa direto
    # print(f"📥 Download: {start_byte}-{end_byte}")
    bytes_enviados = 0
    buffer = bytearray()
    
    try:
        async for chunk in client.iter_download(
            message.media, offset=start_byte, request_size=CHUNK_SIZE, file_size=message.video.size
        ):
            buffer.extend(chunk)
            
            # Flush se atingiu o necessário
            if bytes_enviados + len(buffer) >= bytes_para_enviar:
                restante = bytes_para_enviar - bytes_enviados
                yield bytes(buffer[:restante])
                break
            
            # Flush parcial para manter o fluxo
            if len(buffer) >= MIN_BUFFER:
                yield bytes(buffer)
                bytes_enviados += len(buffer)
                buffer.clear()
        
        # Envia o que sobrou
        if buffer and bytes_enviados < bytes_para_enviar:
            yield bytes(buffer)
            
        background_tasks.add_task(prefetch_chunks, message, end_byte + 1, channel_id, message_id)
                
    except Exception as e:
        print(f"❌ Erro stream: {e}")

# === ROTAS ===

@app.get("/stream/code/{codigo}")
async def stream_por_codigo(
    codigo: str,
    range: Optional[str] = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    """
    Recebe códigos como: pbi-F001, html-F020
    """
    mapeamento = carregar_mapeamento()
    
    # Normaliza código (remove # se vier)
    codigo = codigo.replace('#', '') 
    
    if codigo not in mapeamento:
        raise HTTPException(404, detail=f"Aula {codigo} não mapeada")
    
    dados = mapeamento[codigo]
    message_id = dados["message_id"]
    
    # Tenta pegar channel_id do mapeamento, senão erro
    channel_id = dados.get("channel_id")
    if not channel_id:
        raise HTTPException(500, detail="Mapeamento antigo detectado. Gere o mapeamento novamente.")

    return await processar_video(channel_id, message_id, range, background_tasks)

async def processar_video(channel_id: int, message_id: int, range_header: str, background_tasks: BackgroundTasks):
    try:
        message = await get_message_cached(channel_id, message_id)
        file_size = message.video.size

        if range_header:
            bytes_unit, range_str = range_header.split("=")
            parts = range_str.split("-")
            start = int(parts[0]) if parts[0] else 0
            end = min(int(parts[1]), file_size - 1) if len(parts) > 1 and parts[1] else min(start + RANGE_CHUNK - 1, file_size - 1)
            
            content_length = (end - start) + 1
            headers = {
                'Content-Range': f'bytes {start}-{end}/{file_size}',
                'Accept-Ranges': 'bytes',
                'Content-Length': str(content_length),
                'Content-Type': 'video/mp4',
            }
            
            return StreamingResponse(
                stream_generator(message, start, end, channel_id, message_id, background_tasks),
                status_code=206, headers=headers, media_type="video/mp4"
            )
        else:
            # Fallback para download completo (raro em vídeo player)
            headers = {'Content-Length': str(file_size), 'Content-Type': 'video/mp4'}
            return StreamingResponse(
                client.iter_download(message.media), status_code=200, headers=headers
            )

    except HTTPException: raise
    except Exception as e:
        raise HTTPException(500, detail=str(e))

@app.get("/health")
async def health():
    return {
        "status": "online", 
        "telegram": client.is_connected(),
        "aulas_mapeadas": len(mapeamento_cache) if mapeamento_cache else 0
    }

@app.post("/refresh-map")
async def refresh_map():
    global mapeamento_cache
    mapeamento_cache = None
    carregar_mapeamento()
    return {"status": "Mapeamento recarregado"}