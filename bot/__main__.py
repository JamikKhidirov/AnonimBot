import asyncio

from aiogram.types import BotCommand, BotCommandScopeChat

from bot import bot, dp, logger, set_bot_username
from bot.config import DEVELOPER_ID
from bot.database import init_db, get_or_create_user, get_all_admin_records
from bot.handlers import start, user, admin, anon


USER_COMMANDS = [
    BotCommand(command="start", description="🏠 Главная"),
    BotCommand(command="messages", description="📩 Мои сообщения"),
    BotCommand(command="stop", description="⛔ Выйти из чата"),
    BotCommand(command="help", description="ℹ️ Помощь"),
    BotCommand(command="language", description="🌐 Язык"),
    BotCommand(command="resetlink", description="🔄 Сбросить ссылку"),
]

ADMIN_COMMANDS = USER_COMMANDS + [
    BotCommand(command="admin", description="👮 Админ панель"),
    BotCommand(command="ban", description="⛔ Забанить"),
    BotCommand(command="unban", description="✅ Разбанить"),
    BotCommand(command="banlist", description="📋 Список банов"),
    BotCommand(command="broadcast", description="📢 Рассылка"),
    BotCommand(command="export_csv", description="📤 Экспорт CSV"),
    BotCommand(command="cleanup", description="🧹 Очистка"),
    BotCommand(command="view_user", description="👤 Инфо о пользователе"),
    BotCommand(command="view_messages", description="✉️ Сообщения пользователя"),
    BotCommand(command="sender", description="❓ Отправитель сообщения"),
    BotCommand(command="search_user", description="🔍 Поиск пользователя"),
    BotCommand(command="search_messages", description="🔍 Поиск сообщений"),
    BotCommand(command="show", description="👁 Показать отправителя"),
]


async def main():
    await init_db()

    dev = await get_or_create_user(DEVELOPER_ID, None, None)
    logger.info(f"Developer: {dev.telegram_id} (admin={dev.is_admin}, dev={dev.is_developer})")

    bot_info = await bot.get_me()
    set_bot_username(bot_info.username)
    logger.info(f"Bot started: @{bot_info.username}")

    await bot.set_my_commands(USER_COMMANDS)

    admins = await get_all_admin_records()
    for a in admins:
        try:
            await bot.set_my_commands(ADMIN_COMMANDS, scope=BotCommandScopeChat(chat_id=a.telegram_id))
        except Exception:
            pass

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
