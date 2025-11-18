import asyncio
import json
import os
from collections import deque
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterVideo
from telethon.sessions import StringSession # <--- ADICIONE ESTA LINHA
from fastapi import FastAPI, HTTPException, Header, BackgroundTasks
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from typing import Optional

# === CONFIGURAÇÃO DE PERFIL ===
PERFIL_ATIVO = "ultra_rapido"  # ultra_rapido, rapido, medio, economico

PERFIS = {
    "ultra_rapido": {
        "CHUNK_SIZE": 1024 * 1024,  # 1 MB
        "MIN_BUFFER": 512 * 1024,  # 512 KB
        "RANGE_CHUNK": 50 * 1024 * 1024,  # 50 MB
        "PREFETCH_CHUNKS": 3,  # Baixa 3 chunks adiantado
    },
    "rapido": {
        "CHUNK_SIZE": 512 * 1024,  # 512 KB
        "MIN_BUFFER": 256 * 1024,  # 256 KB
        "RANGE_CHUNK": 20 * 1024 * 1024,  # 20 MB
        "PREFETCH_CHUNKS": 2,  # Baixa 2 chunks adiantado
    },
    "medio": {
        "CHUNK_SIZE": 256 * 1024,  # 256 KB
        "MIN_BUFFER": 128 * 1024,  # 128 KB
        "RANGE_CHUNK": 10 * 1024 * 1024,  # 10 MB
        "PREFETCH_CHUNKS": 1,  # Baixa 1 chunk adiantado
    },
    "economico": {
        "CHUNK_SIZE": 128 * 1024,  # 128 KB
        "MIN_BUFFER": 64 * 1024,  # 64 KB
        "RANGE_CHUNK": 5 * 1024 * 1024,  # 5 MB
        "PREFETCH_CHUNKS": 0,  # Sem prefetch
    }
}

config = PERFIS[PERFIL_ATIVO]
CHUNK_SIZE = config["CHUNK_SIZE"]
MIN_BUFFER = config["MIN_BUFFER"]
RANGE_CHUNK = config["RANGE_CHUNK"]
PREFETCH_CHUNKS = config["PREFETCH_CHUNKS"]

print(f"🎯 Perfil: {PERFIL_ATIVO.upper()}")
print(f"   Chunk: {CHUNK_SIZE / 1024:.0f} KB")
print(f"   Prefetch: {PREFETCH_CHUNKS} chunks adiantado")

# === CONFIGURAÇÃO ===
API_ID = int(os.environ['API_ID'])
API_HASH = os.environ['API_HASH']
SESSION_STRING = os.environ['TELEGRAM_SESSION_STRING'] # <-- NOVO
GRUPO_ALVO = -1001573455897

app = FastAPI()

origins = [
    "http://localhost:3000",
    "http://127.0.0.1:3000",
    "http://127.0.0.1:8000",
    "http://localhost:8000",
    "*"
]

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
mensagens_cache = {}
# NOVO: Cache de chunks (fila de pré-buffering)
chunk_cache = {}  # {(message_id, offset): bytes}


def carregar_mapeamento():
    global mapeamento_cache
    if mapeamento_cache is None:
        if os.path.exists('mapeamento_aulas.json'):
            with open('mapeamento_aulas.json', 'r', encoding='utf-8') as f:
                mapeamento_cache = json.load(f)
                print(f"✅ Mapeamento: {len(mapeamento_cache)} aulas")
        else:
            mapeamento_cache = {}
    return mapeamento_cache


@app.on_event("startup")
async def startup_event():
    await client.start()
    print("✅ Telegram conectado!")
    carregar_mapeamento()

@app.on_event("shutdown")
async def shutdown_event():
    await client.disconnect()


async def get_message_cached(message_id: int):
    """Busca mensagem com cache"""
    if message_id in mensagens_cache:
        return mensagens_cache[message_id]
    
    entity = await client.get_entity(GRUPO_ALVO)
    message = await client.get_messages(entity, ids=message_id)
    
    if not message or not message.video:
        raise HTTPException(404, detail="Vídeo não encontrado")
    
    mensagens_cache[message_id] = message
    return message


# === PRÉ-BUFFERING: Baixa chunks ANTES de pedir ===
async def prefetch_chunks(message, start_offset: int, message_id: int):
    """
    Baixa chunks ADIANTADOS e coloca no cache
    Isso evita lag quando o navegador pedir o próximo chunk!
    """
    if PREFETCH_CHUNKS == 0:
        return  # Perfil econômico não usa prefetch
    
    try:
        # Calcula offsets dos próximos chunks
        offsets = [start_offset + (RANGE_CHUNK * i) for i in range(1, PREFETCH_CHUNKS + 1)]
        
        for offset in offsets:
            # Não baixa se já passou do tamanho do vídeo
            if offset >= message.video.size:
                break
            
            # Não baixa se já está no cache
            cache_key = (message_id, offset)
            if cache_key in chunk_cache:
                continue
            
            # Baixa o chunk e coloca no cache
            end_offset = min(offset + RANGE_CHUNK - 1, message.video.size - 1)
            chunk_data = bytearray()
            
            print(f"🔮 Prefetch: {offset}-{end_offset} ({(end_offset - offset) / (1024*1024):.1f} MB)")
            
            async for chunk in client.iter_download(
                message.media,
                offset=offset,
                request_size=CHUNK_SIZE,
                file_size=message.video.size,
                limit=(end_offset - offset + 1)
            ):
                chunk_data.extend(chunk)
                if len(chunk_data) >= (end_offset - offset + 1):
                    break
            
            # Salva no cache
            chunk_cache[cache_key] = bytes(chunk_data)
            print(f"💾 Chunk {offset} cacheado!")
            
    except Exception as e:
        print(f"⚠️ Erro no prefetch: {e}")


async def stream_generator_with_prefetch(message, start_byte: int, end_byte: int, message_id: int, background_tasks: BackgroundTasks):
    """
    Stream generator COM PRÉ-BUFFERING
    Verifica cache primeiro, depois baixa se necessário
    """
    bytes_para_enviar = (end_byte - start_byte) + 1
    cache_key = (message_id, start_byte)
    
    # VERIFICA SE JÁ ESTÁ NO CACHE (prefetch funcionou!)
    if cache_key in chunk_cache:
        print(f"⚡ CACHE HIT! Chunk {start_byte} já estava pronto!")
        yield chunk_cache[cache_key][:bytes_para_enviar]
        del chunk_cache[cache_key]  # Limpa do cache
        
        # Inicia prefetch dos próximos chunks em background
        background_tasks.add_task(prefetch_chunks, message, end_byte + 1, message_id)
        return
    
    # Se não está no cache, baixa normal
    print(f"📥 Baixando: {start_byte}-{end_byte}")
    bytes_enviados = 0
    buffer = bytearray()
    
    try:
        async for chunk in client.iter_download(
            message.media, 
            offset=start_byte,
            request_size=CHUNK_SIZE,
            file_size=message.video.size
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
        
        # Inicia prefetch dos próximos chunks
        background_tasks.add_task(prefetch_chunks, message, end_byte + 1, message_id)
                
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"❌ Erro: {e}")


async def full_stream_generator(message):
    """Stream completo"""
    buffer = bytearray()
    
    try:
        async for chunk in client.iter_download(
            message.media,
            request_size=CHUNK_SIZE,
            file_size=message.video.size
        ):
            buffer.extend(chunk)
            
            if len(buffer) >= MIN_BUFFER:
                yield bytes(buffer)
                buffer.clear()
        
        if buffer:
            yield bytes(buffer)
            
    except asyncio.CancelledError:
        pass
    except Exception as e:
        print(f"❌ Erro: {e}")


@app.get("/stream/code/{codigo}")
async def stream_por_codigo(
    codigo: str,
    range: Optional[str] = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if not codigo.startswith('#'):
        codigo = f"#{codigo}"
    
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
    """Stream por ID COM PREFETCH"""
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


@app.get("/stream/{identificador}")
async def get_video_stream(
    identificador: str,
    range: Optional[str] = Header(None),
    background_tasks: BackgroundTasks = BackgroundTasks()
):
    if identificador.isdigit():
        return await stream_por_id(int(identificador), range, background_tasks)
    
    if identificador.upper().startswith('F') or identificador.startswith('#F'):
        codigo_limpo = identificador.replace('#', '').upper()
        if codigo_limpo.startswith('F'):
            return await stream_por_codigo(codigo_limpo, range, background_tasks)
    
    raise HTTPException(400, detail="Formato inválido")


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
                videos.append({
                    "id": msg.id,
                    "titulo": titulo,
                    "tamanho_mb": round(msg.video.size / (1024*1024), 2),
                    "duracao_segundos": msg.video.duration
                })
        
        return JSONResponse(content={"total": len(videos), "videos": videos})
        
    except Exception as e:
        raise HTTPException(500, detail=f"Erro: {e}")


@app.get("/health")
async def health_check():
    return JSONResponse(content={
        "status": "ok",
        "perfil": PERFIL_ATIVO,
        "prefetch_chunks": PREFETCH_CHUNKS,
        "telegram_connected": client.is_connected(),
        "mapeamento_loaded": len(carregar_mapeamento()) > 0,
        "cache_mensagens": len(mensagens_cache),
        "cache_chunks": len(chunk_cache)
    })


@app.post("/limpar-cache")
async def limpar_cache():
    global mensagens_cache, mapeamento_cache, chunk_cache
    mensagens_cache.clear()
    chunk_cache.clear()
    mapeamento_cache = None
    carregar_mapeamento()
    return {
        "status": "Cache limpo!", 
        "perfil": PERFIL_ATIVO,
        "prefetch": f"{PREFETCH_CHUNKS} chunks"
    }