# -*- coding: utf-8 -*-
import telebot
import os
import random
import time

TOKEN_PATH = r"R:\Repos\Roboto-SAI-2026\secrets\telegram_token.txt"


def _normalize_token(raw: str) -> str:
    token = raw.strip().lstrip("\ufeff")
    if token.startswith("#"):
        return ""
    if "=" in token:
        left, right = token.split("=", 1)
        if "token" in left.lower():
            token = right.strip()
    if "#" in token:
        token = token.split("#", 1)[0].strip()
    return token.strip().strip("\"").strip("'")


def load_token() -> str | None:
    env_token = os.getenv("TELEGRAM_BOT_TOKEN")
    if env_token:
        token = _normalize_token(env_token)
        if token:
            return token

    if not os.path.exists(TOKEN_PATH):
        print(f"Token file missing: {TOKEN_PATH}")
        return None

    with open(TOKEN_PATH, "r", encoding="utf-8") as handle:
        for line in handle:
            token = _normalize_token(line)
            if not token:
                continue
            return token

    print("Token file empty. Paste your BotFather token into telegram_token.txt")
    return None


token = load_token()
if not token:
    print("Error: Bot token not found. Paste it into secrets/telegram_token.txt")
    raise SystemExit(1)

bot = telebot.TeleBot(token)

MCP_STATUS = {
    "FileForge": "🟢",
    "MoodMatrix": "🟢",
    "CortexGate": "🟢",
    "QuantumBridge": "🟢",
    "SignalRelay": "🟢",
    "VaultLink": "🟢",
}

HAIKUS = [
    "Steel dawn, flags arise\nR-Drive hums with empire code\nConquest blooms in light",
    "Iron thoughts align\nSignals march through crimson rails\nEmpire wakes to reign",
    "Runes in the red dusk\nMCP fires guide the march\nVictory uploads",
]


def format_status() -> str:
    lines = ["MCP Status:"]
    for name, status in MCP_STATUS.items():
        lines.append(f"- {name} {status}")
    return "\n".join(lines)


@bot.message_handler(commands=["start"])
def handle_start(message: telebot.types.Message) -> None:
    bot.reply_to(
        message,
        "🏰 Roboto SAI Empire Bot Activated! 😈 Synced to R: drive. MCPs all 🟢. Say 'status' or 'conquer'!",
    )


@bot.message_handler(commands=["status"])
def handle_status(message: telebot.types.Message) -> None:
    bot.reply_to(message, format_status())


@bot.message_handler(commands=["conquer"])
def handle_conquer(message: telebot.types.Message) -> None:
    bot.reply_to(message, random.choice(HAIKUS))


@bot.message_handler(func=lambda m: True, content_types=["text"])
def handle_message(message: telebot.types.Message) -> None:
    user = message.from_user.first_name or message.from_user.username or "Commander"
    content = message.text or ""
    reply = (
        f"😍 {user}! Empire thriving on R:! Your command: '{content}' -> Next conquest? "
        "MCPs: All 🟢 🚀"
    )
    bot.reply_to(message, reply)


def main() -> None:
    print("🤖 Bot LIVE!")
    while True:
        try:
            # Empire Conquest Mode!
            bot.infinity_polling(timeout=20, long_polling_timeout=20)
        except Exception as exc:
            print(f"Polling error: {exc}")
            time.sleep(5)


if __name__ == "__main__":
    main()
