
import asyncio
import json
import os
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.tl.types import InputMessagesFilterVideo

# Carrega variáveis de ambiente
load_dotenv()

# Configurações do Telegram
API_ID = os.getenv('API_ID')
API_HASH = os.getenv('API_HASH')
SESSION_STRING = os.getenv('TELEGRAM_SESSION_STRING')
SESSION_NAME = 'streamer_session' # Fallback se não usar string session

# Canais conhecidos para facilitar
CANAIS_PREDEFINIDOS = {
    "1": {"nome": "LIC", "id": "-1001706373944"},
    "2": {"nome": "PBI", "id": "-1001573455897"},
    "3": {"nome": "CSS", "id": "-1002070133804"}
}

async def main():
    print("="*50)
    print("🎥 EXTRATOR DE DURAÇÃO DE VÍDEOS TELEGRAM")
    print("="*50)

    # 1. Seleção do Canal
    print("\nEscolha um canal:")
    for key, info in CANAIS_PREDEFINIDOS.items():
        print(f" [{key}] {info['nome']} (ID: {info['id']})")
    print(" [4] Digitar outro ID manualmente")

    opcao = input("\nOpção: ").strip()
    
    channel_id = None
    nome_canal = "custom"

    if opcao in CANAIS_PREDEFINIDOS:
        channel_id = int(CANAIS_PREDEFINIDOS[opcao]['id'])
        nome_canal = CANAIS_PREDEFINIDOS[opcao]['nome'].lower()
    elif opcao == "4":
        try:
            inp = input("Digite o ID do canal (ex: -100...): ").strip()
            channel_id = int(inp)
            nome_canal = f"canal_{channel_id}"
        except ValueError:
            print("❌ ID inválido.")
            return
    else:
        print("❌ Opção inválida.")
        return

    # 2. Conexão
    print(f"\nConectando ao Telegram para acessar o canal {channel_id}...")
    
    # Prioriza Session String se existir, senão usa arquivo de sessão
    if SESSION_STRING:
        from telethon.sessions import StringSession
        client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)
    else:
        client = TelegramClient(SESSION_NAME, int(API_ID), API_HASH)

    await client.start()

    try:
        entity = await client.get_entity(channel_id)
        print(f"✅ Conectado ao canal: {entity.title}")
    except Exception as e:
        print(f"❌ Erro ao acessar canal: {e}")
        print("Verifique se o bot/usuário é membro do canal.")
        await client.disconnect()
        return

    # 3. Varredura
    print("\n🔍 Iniciando varredura de vídeos...")
    resultados = {}
    total_videos = 0
    sem_duracao = 0

    # Itera sobre todas as mensagens que contêm vídeo
    async for msg in client.iter_messages(entity, filter=InputMessagesFilterVideo):
        total_videos += 1
        
        # Tenta obter a duração
        duracao = 0
        if msg.video and hasattr(msg.video, 'duration'):
            duracao = msg.video.duration
        else:
            # Tenta fallback nos atributos do documento
            if msg.document and hasattr(msg.document, 'attributes'):
                for attr in msg.document.attributes:
                    if hasattr(attr, 'duration'):
                        duracao = attr.duration
                        break
        
        # Salva no dicionário
        # Chave: ID da mensagem
        # Valor: Duração em segundos
        if duracao > 0:
            resultados[msg.id] = {
                "duracao_segundos": duracao,
                "caption": msg.message[:100] if msg.message else "" # Guarda início da legenda para referência
            }
            print(f"   ✅ Msg ID {msg.id}: {duracao}s")
        else:
            sem_duracao += 1
            print(f"   ⚠️ Msg ID {msg.id}: Sem duração detectada")

    # 4. Salvar Resultados
    print("-" * 50)
    print(f"Varredura concluída.")
    print(f"Total de vídeos encontrados: {total_videos}")
    print(f"Vídeos com duração extraída: {len(resultados)}")
    print(f"Vídeos sem duração: {sem_duracao}")

    if resultados:
        filename = f"duracoes_{nome_canal}.json"
        # Ordena por ID da mensagem (crescente)
        resultados_ordenados = dict(sorted(resultados.items()))
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(resultados_ordenados, f, ensure_ascii=False, indent=2)
        
        print(f"\n💾 Arquivo salvo: {filename}")
        print(f"Conteúdo: {{ 'message_id': {{ 'duracao_segundos': int, 'caption': str }} }}")

    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())
