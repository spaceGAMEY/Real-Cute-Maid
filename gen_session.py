"""
Запусти этот файл ОДИН РАЗ у себя (не на хосте), чтобы получить SESSION_STRING.
Он спросит номер телефона и код из Telegram, а потом выведет длинную строку.
Эту строку вставь в config.py. Никому её не показывай: это доступ к твоему аккаунту.
"""
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = int(input("Введи API_ID: ").strip())
api_hash = input("Введи API_HASH: ").strip()

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("\nТВОЙ SESSION_STRING (скопируй целиком):\n")
    print(client.session.save())
    print()
