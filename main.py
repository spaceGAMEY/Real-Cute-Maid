import asyncio
import json
import os
import random
import re
import time

from telethon import TelegramClient, events
from telethon.sessions import StringSession

try:
    import config
except ImportError:
    config = None


def get(name, default=""):
    """Сначала берём из переменных окружения хоста, потом из config.py."""
    value = os.environ.get(name)
    if value:
        return value
    return getattr(config, name, default) if config else default


API_ID = str(get("API_ID", "")).strip()
API_HASH = str(get("API_HASH", "")).strip()
SESSION_STRING = str(get("SESSION_STRING", "")).strip()

if not API_ID.isdigit() or not API_HASH or not SESSION_STRING \
        or API_ID == "12345678" or "ВСТАВЬ" in SESSION_STRING:
    raise SystemExit(
        "Заполни API_ID, API_HASH и SESSION_STRING в config.py "
        "(или в переменных окружения хоста). Подробности в README.txt"
    )

SETTINGS_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settings.json")

DEFAULTS = {
    "enabled": True,
    "text": "Привет! Сейчас я не на связи, отвечу позже.",
    "cooldown_hours": 12,   # как часто можно отвечать одному и тому же человеку
    "replied": {},          # id пользователя -> время последнего автоответа
}


def load_settings():
    try:
        with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def save_settings():
    with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(S, f, ensure_ascii=False, indent=2)


S = load_settings()

client = TelegramClient(StringSession(SESSION_STRING), int(API_ID), API_HASH)

HELP = (
    "🤖 Команды автоответчика (пиши их сюда, в «Избранное»):\n\n"
    "/set ТЕКСТ — задать текст автоответа\n"
    "/on — включить\n"
    "/off — выключить\n"
    "/status — показать текущие настройки\n"
    "/cooldown N — отвечать одному человеку не чаще раза в N часов\n"
    "/reset — забыть, кому уже отвечал (ответит всем заново)\n"
    "/help — эта справка"
)


# ---------- Управление: команды в «Избранном» ----------
@client.on(events.NewMessage(chats="me", pattern=re.compile(r"^/\w+", re.S)))
async def commands(event):
    text = event.raw_text.strip()
    cmd, _, arg = text.partition(" ")
    cmd = cmd.lower()
    arg = arg.strip()
    # Если команда с новой строки, а не через пробел
    if "\n" in cmd:
        cmd, _, rest = cmd.partition("\n")
        arg = (rest + " " + arg).strip()

    if cmd == "/set":
        if not arg:
            await event.respond("⚠️ Напиши текст после команды, например:\n/set Привет! Отвечу вечером.")
            return
        S["text"] = arg
        save_settings()
        await event.respond("✅ Текст автоответа обновлён:\n\n" + arg)

    elif cmd == "/on":
        S["enabled"] = True
        save_settings()
        await event.respond("✅ Автоответчик включён.")

    elif cmd == "/off":
        S["enabled"] = False
        save_settings()
        await event.respond("⏸ Автоответчик выключен.")

    elif cmd == "/cooldown":
        try:
            hours = float(arg.replace(",", "."))
            if hours < 0:
                raise ValueError
        except ValueError:
            await event.respond("⚠️ Укажи число часов, например: /cooldown 6")
            return
        S["cooldown_hours"] = hours
        save_settings()
        await event.respond(f"✅ Теперь отвечаю одному человеку не чаще раза в {hours:g} ч.")

    elif cmd == "/reset":
        S["replied"] = {}
        save_settings()
        await event.respond("✅ Список «кому уже отвечал» очищен.")

    elif cmd == "/status":
        state = "включён ✅" if S["enabled"] else "выключен ⏸"
        await event.respond(
            f"📊 Автоответчик {state}\n"
            f"Повтор для одного человека: раз в {S['cooldown_hours']:g} ч.\n"
            f"Людей в списке ответов: {len(S['replied'])}\n\n"
            f"Текст:\n{S['text']}"
        )

    elif cmd in ("/help", "/start"):
        await event.respond(HELP)


# ---------- Сам автоответ ----------
@client.on(events.NewMessage(incoming=True))
async def auto_reply(event):
    if not event.is_private or not S["enabled"]:
        return

    sender = await event.get_sender()
    if sender is None or getattr(sender, "bot", False):
        return
    if sender.id == 777000:  # служебные сообщения Telegram (коды входа)
        return

    key = str(sender.id)
    now = time.time()
    last = S["replied"].get(key, 0)
    if now - last < S["cooldown_hours"] * 3600:
        return

    S["replied"][key] = now
    save_settings()

    await asyncio.sleep(random.uniform(1, 3))  # небольшая пауза, чтобы выглядело естественно
    await event.reply(S["text"])


async def main():
    await client.start()
    me = await client.get_me()
    print(f"Автоответчик запущен от имени: {me.first_name} (id {me.id})")
    await client.send_message("me", "🟢 Автоответчик запущен. Напиши /help, чтобы увидеть команды.")
    await client.run_until_disconnected()


if __name__ == "__main__":
    client.loop.run_until_complete(main())
