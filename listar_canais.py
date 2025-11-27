import asyncio
import os                                  # <--- NOVO
from dotenv import load_dotenv             # <--- NOVO
from telethon import TelegramClient

load_dotenv()

# Suas credenciais
API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')
SESSION_NAME = 'streamer_session'

async def main():
    async with TelegramClient(SESSION_NAME, API_ID, API_HASH) as client:
        print("📋 Listando seus canais e grupos...")
        print("-" * 60)
        async for dialog in client.iter_dialogs():
            # Filtra apenas canais e grupos
            if dialog.is_channel or dialog.is_group:
                print(f"Nome: {dialog.name}")
                print(f"ID: {dialog.id}")
                print("-" * 60)

if __name__ == '__main__':
    asyncio.run(main())