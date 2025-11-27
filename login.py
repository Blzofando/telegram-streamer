import asyncio
import asyncio
import os                                  # <--- NOVO
from dotenv import load_dotenv             # <--- NOVO
from telethon import TelegramClient

load_dotenv()

# SUBSTITUA PELOS SEUS DADOS (Agora vindos do .env)
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_NAME = 'streamer_session'

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