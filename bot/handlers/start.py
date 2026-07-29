from aiogram import F
from aiogram.filters import CommandStart
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot, dp, get_bot_username
from bot.database import (
    get_or_create_user, get_or_create_link, get_link_by_code, set_active_session,
    get_or_create_referral_code, process_referral, get_referral_count,
)
from bot.locales import t
from bot.keyboards import stop_session_kb


def _link_kb(url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Открыть ссылку", url=url),
         InlineKeyboardButton(text="📋 Поделиться", url=f"https://t.me/share/url?url={url}")],
    ])


def _start_kb(share_url: str, ref_url: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔗 Моя ссылка", url=share_url),
         InlineKeyboardButton(text="📋 Поделиться", url=f"https://t.me/share/url?url={share_url}")],
        [InlineKeyboardButton(text="👥 Пригласить друга", url=f"https://t.me/share/url?url={ref_url}&text=🎁 Привет! Переходи по этой ссылке и пиши мне анонимно!")],
        [InlineKeyboardButton(text="🎁 Бонусы", callback_data="bonuses")],
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

    text = (
        t("start_text", lang).format(link=share_url)
    )
    await message.answer(text, reply_markup=_start_kb(share_url, ref_url))


async def _handle_referral(message: Message, user, code: str, lang: str):
    referrer = await process_referral(message.from_user.id, code)

    link = await get_or_create_link(user.id)
    share_url = f"https://t.me/{get_bot_username()}?start={link.code}"

    if referrer:
        owner_lang = referrer.language or "ru"
        await bot.send_message(
            referrer.telegram_id,
            t("referral_bonus_gained", owner_lang),
        )
        text = t("referral_text", lang).format(link=share_url)

        referrer_link = await get_or_create_link(referrer.id)
        write_to_referrer_url = f"https://t.me/{get_bot_username()}?start={referrer_link.code}"

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="💬 Написать пригласившему", url=write_to_referrer_url)],
            [InlineKeyboardButton(text="🔗 Моя ссылка", url=share_url),
             InlineKeyboardButton(text="📋 Поделиться", url=f"https://t.me/share/url?url={share_url}")],
            [InlineKeyboardButton(text="🎁 Бонусы", callback_data="bonuses")],
        ])
        await message.answer(text, reply_markup=kb)
        return

    ref_code = await get_or_create_referral_code(message.from_user.id)
    ref_url = f"https://t.me/{get_bot_username()}?start={ref_code}"

    text = t("start_text", lang).format(link=share_url)
    await message.answer(text, reply_markup=_start_kb(share_url, ref_url))


async def _handle_deep_link(message: Message, user, code: str, lang: str):
    link = await get_link_by_code(code)
    if not link:
        await message.answer(t("session_expired", lang))
        return

    if user.id == link.user_id:
        share_url = f"https://t.me/{get_bot_username()}?start={link.code}"

        ref_code = await get_or_create_referral_code(message.from_user.id)
        ref_url = f"https://t.me/{get_bot_username()}?start={ref_code}"

        await message.answer(
            t("start_text", lang).format(link=share_url),
            reply_markup=_start_kb(share_url, ref_url),
        )
        return

    await set_active_session(message.from_user.id, code)
    await message.answer(t("chat_started", lang), reply_markup=stop_session_kb(lang))
    owner_lang = link.user.language or "ru"
    await bot.send_message(
        link.user.telegram_id,
        t("new_visitor", owner_lang),
    )


@dp.callback_query(F.data == "bonuses")
async def bonuses_callback(cb):
    try:
        await cb.answer()
        user = await get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.full_name)
        lang = user.language or "ru"

        ref_code = await get_or_create_referral_code(cb.from_user.id)
        ref_url = f"https://t.me/{get_bot_username()}?start={ref_code}"
        ref_count = await get_referral_count(cb.from_user.id)

        from datetime import datetime
        if user.referral_bonus_until and user.referral_bonus_until > datetime.utcnow():
            remaining = user.referral_bonus_until - datetime.utcnow()
            days = remaining.days
            hours = remaining.seconds // 3600
            bonus_status = f"✅ <b>Активен</b> — ещё {days}д {hours}ч"
        else:
            bonus_status = "❌ <b>Неактивен</b>"

        text = (
            "🎁 <b>Твои бонусы</b>\n\n"
            f"👥 Приглашено друзей: <b>{ref_count}</b>\n"
            f"👁 Просмотр отправителей: {bonus_status}\n\n"
            "━━━━━━━━━━━━━━━\n"
            "📋 <b>Твоя реферальная ссылка:</b>\n"
            f"<code>{ref_url}</code>\n\n"
            "Скопируй и отправь другу!\n"
            "За каждого друга ты получишь <b>+3 дня</b> просмотра."
        )

        from bot.keyboards import back_kb
        await cb.message.edit_text(text, reply_markup=back_kb("start"))
    except Exception as e:
        import logging
        logging.exception(f"bonuses_callback error")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


@dp.callback_query(F.data == "start")
async def start_back_callback(cb):
    try:
        await cb.answer()
        user = await get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.full_name)
        lang = user.language or "ru"

        link = await get_or_create_link(user.id)
        share_url = f"https://t.me/{get_bot_username()}?start={link.code}"

        ref_code = await get_or_create_referral_code(cb.from_user.id)
        ref_url = f"https://t.me/{get_bot_username()}?start={ref_code}"

        text = t("start_text", lang).format(link=share_url)
        await cb.message.edit_text(text, reply_markup=_start_kb(share_url, ref_url))
    except Exception as e:
        import logging
        logging.exception(f"start_back_callback error")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass
