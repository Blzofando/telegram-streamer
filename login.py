import asyncio
from telethon import TelegramClient

# SUBSTITUA PELOS SEUS DADOS
API_ID = 25657270                # Coloque seu api_id aqui (como um número, sem aspas)
API_HASH = 'f2d5b9d5c89471989432ef1c2ee22993'   # Coloque seu api_hash aqui (entre aspas)
SESSION_NAME = 'streamer_session' # Nome do arquivo de sessão que será criado

async def main():
    print("Iniciando login para criar a sessão...")
    
    # O client será criado e tentará se conectar
    client = TelegramClient(SESSION_NAME, API_ID, API_HASH)
    await client.start()
    
    print(f"Login bem-sucedido! O arquivo '{SESSION_NAME}.session' foi criado.")
    print("Você não precisa mais rodar este script.")
    
    await client.disconnect()

if __name__ == "__main__":
    asyncio.run(main())