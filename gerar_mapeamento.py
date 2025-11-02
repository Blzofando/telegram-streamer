import asyncio
import json
import re
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterVideo

# --- Configuração ---
API_ID = 25657270
API_HASH = 'f2d5b9d5c89471989432ef1c2ee22993'
SESSION_NAME = 'streamer_session'
GRUPO_ALVO = -1001573455897

async def gerar_mapeamento():
    """
    Gera um arquivo JSON com o mapeamento:
    código (#F001, #F002, etc) -> ID da mensagem
    
    Execute este script UMA VEZ para criar o mapeamento.
    Depois use o JSON no seu site!
    """
    print("🔍 Conectando ao Telegram...")
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    
    print("📥 Buscando todos os vídeos do canal...")
    entity = await client.get_entity(GRUPO_ALVO)
    
    mapeamento = {}
    videos_encontrados = 0
    videos_sem_codigo = 0
    
    # Busca TODOS os vídeos (limite alto)
    async for msg in client.iter_messages(
        entity, 
        limit=500,  # Ajuste se tiver mais de 500 vídeos
        filter=InputMessagesFilterVideo
    ):
        if msg and msg.video and msg.message:
            # Procura por códigos no formato #F001, #F002, etc
            # Usando regex para encontrar #F seguido de números
            match = re.search(r'#F(\d+)', msg.message)
            
            if match:
                codigo = f"#F{match.group(1)}"  # Ex: #F001
                
                # Extrai o título completo (remove hashtags extras se houver)
                titulo = msg.message.strip()
                
                # Pega o tamanho de forma segura
                try:
                    tamanho = msg.video.size if hasattr(msg.video, 'size') else msg.file.size
                    tamanho_mb = round(tamanho / (1024*1024), 2)
                except:
                    tamanho_mb = 0
                
                # Pega a duração de forma segura
                duracao = 0
                try:
                    # Tenta pegar do atributo video primeiro
                    if hasattr(msg.video, 'duration') and msg.video.duration:
                        duracao = msg.video.duration
                    # Se não tiver, tenta do documento
                    elif hasattr(msg, 'document') and hasattr(msg.document, 'attributes'):
                        for attr in msg.document.attributes:
                            if hasattr(attr, 'duration'):
                                duracao = attr.duration
                                break
                except:
                    duracao = 0
                
                mapeamento[codigo] = {
                    "message_id": msg.id,
                    "titulo_completo": titulo,
                    "tamanho_mb": tamanho_mb,
                    "duracao": duracao
                }
                
                videos_encontrados += 1
                duracao_str = f"{duracao}s" if duracao > 0 else "N/A"
                print(f"✅ {codigo} -> ID {msg.id} | {tamanho_mb}MB | {duracao_str} | {titulo[:40]}...")
            else:
                videos_sem_codigo += 1
                # print(f"⚠️  Vídeo sem código #F: ID {msg.id} | {msg.message[:40]}...")
    
    # Salva em arquivo JSON
    with open('mapeamento_aulas.json', 'w', encoding='utf-8') as f:
        json.dump(mapeamento, f, ensure_ascii=False, indent=2)
    
    print(f"\n{'='*60}")
    print(f"🎉 Mapeamento gerado com sucesso!")
    print(f"{'='*60}")
    print(f"📊 Total de vídeos com código #F: {videos_encontrados}")
    print(f"⚠️  Vídeos sem código #F: {videos_sem_codigo}")
    print(f"💾 Arquivo salvo: mapeamento_aulas.json")
    
    # Exibe exemplo de como usar
    if mapeamento:
        print(f"\n{'='*60}")
        print("📖 Exemplo de uso:")
        print(f"{'='*60}")
        primeiro_codigo = list(mapeamento.keys())[0]
        primeiro_id = mapeamento[primeiro_codigo]["message_id"]
        print(f"   Código: {primeiro_codigo}")
        print(f"   URL no navegador: http://127.0.0.1:8000/stream/code/{primeiro_codigo.replace('#', '')}")
        print(f"   URL no seu site: http://seu-site.com/stream/code/{primeiro_codigo.replace('#', '')}")
        print(f"\n   Ou use o ID direto: http://127.0.0.1:8000/stream/{primeiro_id}")
        
        # Mostra os primeiros 5 códigos encontrados
        print(f"\n{'='*60}")
        print("📋 Primeiros códigos encontrados:")
        print(f"{'='*60}")
        for i, (codigo, dados) in enumerate(list(mapeamento.items())[:5]):
            print(f"   {codigo} -> {dados['titulo_completo'][:50]}...")
    else:
        print("\n⚠️  ATENÇÃO: Nenhum vídeo com código #F foi encontrado!")
        print("   Verifique se os vídeos no Telegram têm códigos como #F001, #F002, etc.")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(gerar_mapeamento())