import os
import sys

from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
raw_dev_id = os.getenv("DEVELOPER_ID", "0")
try:
    DEVELOPER_ID: int = int(raw_dev_id)
except ValueError:
    print(f"ERROR: DEVELOPER_ID в .env должно быть числом, а у тебя '{raw_dev_id}'")
    print("Узнай свой Telegram ID (например, через @userinfobot) и запиши в .env")
    sys.exit(1)

if not BOT_TOKEN:
    print("ERROR: BOT_TOKEN в .env не указан")
    sys.exit(1)

DATABASE_URL: str = "sqlite+aiosqlite:///anonim_bot.db"
