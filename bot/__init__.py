import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from bot.config import BOT_TOKEN

logging.basicConfig(level=logging.INFO, stream=sys.stdout, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("AnonimBot")

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.HTML))
dp = Dispatcher()

_bot_username: str | None = None

def set_bot_username(username: str):
    global _bot_username
    _bot_username = username

def get_bot_username() -> str:
    return _bot_username or "bot"
