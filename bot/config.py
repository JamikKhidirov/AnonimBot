import os
import sys

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

for name in (".env", ".env.example"):
    p = os.path.join(BASE_DIR, name)
    if os.path.isfile(p):
        load_dotenv(p)
        break

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
