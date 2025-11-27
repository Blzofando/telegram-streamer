import asyncio
import json
import re
import os                                  # <--- NOVO
from dotenv import load_dotenv             # <--- NOVO
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterVideo

load_dotenv()                              # <--- Carrega o arquivo .env

# --- CONFIGURAÇÃO DE CREDENCIAIS ---
API_ID = int(os.getenv('API_ID'))          # <--- Pega do .env
API_HASH = os.getenv('API_HASH')           # <--- Pega do .env
SESSION_NAME = 'streamer_session'

# --- CONFIGURAÇÃO DOS CURSOS ---
# Coloque aqui o Prefixo (que vai na URL) e o ID do Canal correspondente
CANAIS_CURSOS = {
    "pbi": -1001573455897,      # Seu canal atual de Power BI
    "lic": -1001706373944,     # SUBSTITUA PELO ID DO CANAL DE Licitante Extremo
    # "js": -1009876543210      # Exemplo para adicionar mais cursos
}

async def gerar_mapeamento():
    print("🔍 Conectando ao Telegram...")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    
    mapeamento_global = {}
    
    # Loop pelos canais configurados
    for prefixo, channel_id in CANAIS_CURSOS.items():
        print(f"\n📡 Mapeando curso: {prefixo.upper()} (ID: {channel_id})")
        
        try:
            entity = await client.get_entity(channel_id)
        except Exception as e:
            print(f"❌ Erro ao acessar canal {channel_id}: {e}")
            continue

        videos_encontrados = 0
        
        async for msg in client.iter_messages(entity, limit=1000, filter=InputMessagesFilterVideo):
            if msg and msg.video and msg.message:
                # Procura por #F seguido de números na legenda do Telegram
                match = re.search(r'#F(\d+)', msg.message)
                
                if match:
                    numero_aula = match.group(1) # Ex: 001
                    
                    # --- CRIAÇÃO DA CHAVE COM O PREFIXO ---
                    # Se no telegram é #F001 e o prefixo é 'pbi', a chave vira 'pbi-F001'
                    codigo_chave = f"{prefixo}-F{numero_aula}" 
                    
                    # Tenta pegar duração
                    duracao = 0
                    if hasattr(msg.video, 'duration'):
                        duracao = msg.video.duration
                    
                    # Salva no mapeamento INCLUINDO O CHANNEL_ID
                    mapeamento_global[codigo_chave] = {
                        "message_id": msg.id,
                        "channel_id": channel_id, # <--- IMPORTANTE: Salva a origem
                        "titulo_completo": msg.message.strip(),
                        "tamanho_mb": round(msg.video.size / (1024*1024), 2),
                        "duracao": duracao
                    }
                    
                    videos_encontrados += 1
                    print(f"   ✅ {codigo_chave} -> ID {msg.id}")
        
        print(f"   📊 Total em {prefixo}: {videos_encontrados}")

    # Salva o arquivo JSON final com todos os cursos
    with open('mapeamento_aulas.json', 'w', encoding='utf-8') as f:
        json.dump(mapeamento_global, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"🎉 Mapeamento COMPLETO gerado!")
    print(f"💾 Arquivo: mapeamento_aulas.json")
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(gerar_mapeamento())