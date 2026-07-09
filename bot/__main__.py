import asyncio

from bot import bot, dp, logger, set_bot_username
from bot.config import DEVELOPER_ID
from bot.database import init_db, get_or_create_user
from bot.handlers import start, user, admin, anon


async def main():
    await init_db()

    dev = await get_or_create_user(DEVELOPER_ID, None, None)
    logger.info(f"Developer: {dev.telegram_id} (admin={dev.is_admin}, dev={dev.is_developer})")

    bot_info = await bot.get_me()
    set_bot_username(bot_info.username)
    logger.info(f"Bot started: @{bot_info.username}")

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
