from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot, dp, get_bot_username
from bot.database import (
    get_or_create_user, get_or_create_link, get_link_by_code, set_active_session,
)
from bot.locales import t


def _link_kb(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Открыть ссылку", url=url),
         InlineKeyboardButton(text="📋 Поделиться", url=f"https://t.me/share/url?url={url}")],
    ])


@dp.message(CommandStart())
async def start_handler(message: Message, command: CommandStart):
    user = await get_or_create_user(
        message.from_user.id,
        message.from_user.username,
        message.from_user.full_name,
    )
    lang = user.language or "ru"

    code = command.args
    if code:
        await _handle_deep_link(message, user, code, lang)
        return

    link = await get_or_create_link(user.id)
    share_url = f"https://t.me/{get_bot_username()}?start={link.code}"
    await message.answer(
        t("start_text", lang).format(link=share_url),
        reply_markup=_link_kb(share_url),
    )


async def _handle_deep_link(message: Message, user, code: str, lang: str):
    link = await get_link_by_code(code)
    if not link:
        await message.answer(t("session_expired", lang))
        return

    if user.id == link.user_id:
        link_obj = await get_or_create_link(user.id)
        share_url = f"https://t.me/{get_bot_username()}?start={link_obj.code}"
        await message.answer(
            t("start_text", lang).format(link=share_url),
            reply_markup=_link_kb(share_url),
        )
        return

    await set_active_session(message.from_user.id, code)
    await message.answer(t("chat_started", lang))
    await bot.send_message(
        link.user.telegram_id,
        "Кто-то перешёл по твоей ссылке и теперь может писать тебе анонимно!",
    )
