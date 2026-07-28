from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot, dp, get_bot_username
from bot.database import (
    get_or_create_user, get_or_create_link, get_link_by_code, set_active_session,
    get_or_create_referral_code, process_referral,
)
from bot.locales import t
from bot.keyboards import stop_session_kb


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
        if code.startswith("ref_"):
            await _handle_referral(message, user, code, lang)
            return
        await _handle_deep_link(message, user, code, lang)
        return

    link = await get_or_create_link(user.id)
    share_url = f"https://t.me/{get_bot_username()}?start={link.code}"

    ref_code = await get_or_create_referral_code(message.from_user.id)
    ref_url = f"https://t.me/{get_bot_username()}?start={ref_code}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Моя ссылка", url=share_url),
         InlineKeyboardButton(text="📋 Поделиться", url=f"https://t.me/share/url?url={share_url}")],
        [InlineKeyboardButton(text="👥 Пригласить друга", url=f"https://t.me/share/url?url={ref_url}&text=🎁 Привет! Переходи по этой ссылке и пиши мне анонимно!")],
    ])

    text = (
        t("start_text", lang).format(link=share_url) + "\n\n"
        + t("referral_info", lang).format(link=ref_url)
    )
    await message.answer(text, reply_markup=kb)


async def _handle_referral(message: Message, user, code: str, lang: str):
    referrer = await process_referral(message.from_user.id, code)
    link = await get_or_create_link(user.id)
    share_url = f"https://t.me/{get_bot_username()}?start={link.code}"

    ref_code = await get_or_create_referral_code(message.from_user.id)
    ref_url = f"https://t.me/{get_bot_username()}?start={ref_code}"

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Моя ссылка", url=share_url),
         InlineKeyboardButton(text="📋 Поделиться", url=f"https://t.me/share/url?url={share_url}")],
        [InlineKeyboardButton(text="👥 Пригласить друга", url=f"https://t.me/share/url?url={ref_url}&text=🎁 Привет! Переходи по этой ссылке и пиши мне анонимно!")],
    ])

    text = (
        t("start_text", lang).format(link=share_url)
    )

    if referrer:
        owner_lang = referrer.language or "ru"
        await bot.send_message(
            referrer.telegram_id,
            t("referral_bonus_gained", owner_lang),
        )
        text += "\n\n" + t("referral_welcome", lang)

    await message.answer(text, reply_markup=kb)


async def _handle_deep_link(message: Message, user, code: str, lang: str):
    link = await get_link_by_code(code)
    if not link:
        await message.answer(t("session_expired", lang))
        return

    if user.id == link.user_id:
        link_obj = await get_or_create_link(user.id)
        share_url = f"https://t.me/{get_bot_username()}?start={link_obj.code}"

        ref_code = await get_or_create_referral_code(message.from_user.id)
        ref_url = f"https://t.me/{get_bot_username()}?start={ref_code}"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="🔗 Моя ссылка", url=share_url),
             InlineKeyboardButton(text="📋 Поделиться", url=f"https://t.me/share/url?url={share_url}")],
            [InlineKeyboardButton(text="👥 Пригласить друга", url=f"https://t.me/share/url?url={ref_url}&text=🎁 Привет! Переходи по этой ссылке и пиши мне анонимно!")],
        ])

        await message.answer(
            t("start_text", lang).format(link=share_url),
            reply_markup=kb,
        )
        return

    await set_active_session(message.from_user.id, code)
    await message.answer(t("chat_started", lang), reply_markup=stop_session_kb(lang))
    owner_lang = link.user.language or "ru"
    await bot.send_message(
        link.user.telegram_id,
        t("new_visitor", owner_lang),
    )
