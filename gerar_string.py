import os                                  # <--- NOVO
from dotenv import load_dotenv             # <--- NOVO
from telethon.sync import TelegramClient
from telethon.sessions import StringSession

load_dotenv()

API_ID = int(os.getenv('API_ID'))
API_HASH = os.getenv('API_HASH')

# O resto continua igual:
with TelegramClient(StringSession(), API_ID, API_HASH) as client:
    print("SESSION_STRING =", client.session.save())