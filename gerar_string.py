import os
import asyncio
from dotenv import load_dotenv
from telethon import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')

async def main():
    # Iniciando o cliente para gerar a sessão interativamente
    client = TelegramClient(StringSession(), API_ID, API_HASH)
    await client.start()
    print("SESSION_STRING =", client.session.save())
    await client.disconnect()

if __name__ == '__main__':
    asyncio.run(main())