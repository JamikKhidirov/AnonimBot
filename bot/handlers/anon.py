import logging
import html

from aiogram import F
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot, dp, get_bot_username
from bot.database import (
    get_active_session, clear_active_session,
    get_link_by_code, get_link_by_id,
    get_message_by_id, get_forwarded_message, get_last_forwarded_for_user,
    save_forwarded_message,
    create_message, is_banned, get_or_create_user,
    get_or_create_link, reset_link, set_user_language,
)
from bot.locales import t
from bot.keyboards import reset_link_kb

logger = logging.getLogger(__name__)


@dp.message(F.text, ~F.reply_to_message)
async def handle_anonymous_message(message: Message):
    if await is_banned(message.from_user.id):
        user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
        await message.answer(t("you_banned", user.language or "ru"))
        return

    session = await get_active_session(message.from_user.id)
    if not session:
        user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
        await message.answer(t("no_session", user.language or "ru"))
        return

    link = await get_link_by_code(session.link_code)
    if not link:
        await clear_active_session(message.from_user.id)
        user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
        await message.answer(t("session_expired", user.language or "ru"))
        return

    msg = await create_message(
        link_id=link.id,
        sender_id=message.from_user.id,
        text=message.text,
        sender_username=message.from_user.username,
        sender_full_name=message.from_user.full_name,
    )

    sender_user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(t("msg_sent", sender_user.language or "ru"))

    owner = link.user
    owner_text = t("new_anon", owner.language or "ru").format(text=message.text)

    if owner.is_admin or owner.is_developer:
        whois_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("whois_btn", owner.language or "ru"), callback_data=f"whois:{msg.id}")],
        ])
        sent = await bot.send_message(owner.telegram_id, owner_text, reply_markup=whois_kb)
    else:
        sent = await bot.send_message(owner.telegram_id, owner_text)

    await save_forwarded_message(sent.message_id, owner.telegram_id, msg.id)

    logger.info(
        f"ANON: sender={message.from_user.id} "
        f"(@{message.from_user.username}) -> owner={owner.telegram_id} "
        f"(@{owner.username}): {message.text[:100]}"
    )


@dp.message(F.text, F.reply_to_message)
async def handle_reply_to_anonymous(message: Message):
    replied = message.reply_to_message
    if not replied or replied.from_user.id != bot.id:
        return

    me_user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    lang = me_user.language or "ru"

    forwarded = await get_forwarded_message(replied.message_id, message.from_user.id)
    if not forwarded:
        return

    original = await get_message_by_id(forwarded.original_msg_id)
    if not original:
        await message.answer(t("original_not_found", lang))
        return

    link = await get_link_by_id(original.link_id)
    if not link:
        await message.answer(t("link_not_found", lang))
        return

    owner = link.user

    quote_text = html.escape(original.text)
    reply_text = html.escape(message.text)

    if message.from_user.id == owner.telegram_id:
        recipient_id = original.sender_id
        header = t("reply_owner_header", owner.language or "ru")
        log_dir = "owner->sender"
    else:
        recipient_id = owner.telegram_id
        header = t("reply_sender_header", owner.language or "ru")
        log_dir = "sender->owner"

    prev = await get_last_forwarded_for_user(recipient_id, original.id)
    reply_to = prev.bot_message_id if prev else None

    body = f"{header}\n\n<blockquote>{quote_text}</blockquote>\n\n{reply_text}"

    if log_dir == "sender->owner" and (owner.is_admin or owner.is_developer):
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("whois_btn", owner.language or "ru"), callback_data=f"whois:{original.id}")],
        ])
        sent = await bot.send_message(recipient_id, body, reply_to_message_id=reply_to, reply_markup=kb)
    else:
        sent = await bot.send_message(recipient_id, body, reply_to_message_id=reply_to)

    await save_forwarded_message(sent.message_id, recipient_id, original.id, message.text)
    await message.answer(t("reply_sent", lang))

    logger.info(
        f"REPLY ({log_dir}): {message.from_user.id} "
        f"(@{message.from_user.username}) -> {recipient_id}: "
        f"{message.text[:100]}"
    )


@dp.callback_query(F.data == "reset_link")
async def reset_link_callback(cb):
    try:
        await cb.answer()
        user = await get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.full_name)
        lang = user.language or "ru"

        new_link = await reset_link(cb.from_user.id)
        if not new_link:
            await cb.message.edit_text("Ошибка создания ссылки.")
            return

        share_url = f"https://t.me/{get_bot_username()}?start={new_link.code}"
        from bot.handlers.start import _link_kb
        await cb.message.edit_text(
            t("reset_link_done", lang).format(link=share_url),
            reply_markup=_link_kb(share_url),
        )
    except Exception as e:
        logger.exception(f"reset_link_callback error")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


@dp.callback_query(F.data == "cancel_reset")
async def cancel_reset_callback(cb):
    try:
        await cb.answer()
        user = await get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.full_name)
        await cb.message.edit_text(t("link_reset_cancelled", user.language or "ru"))
    except Exception as e:
        logger.exception(f"cancel_reset_callback error")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


@dp.callback_query(F.data.startswith("lang:"))
async def lang_callback(cb):
    try:
        await cb.answer()
        lang = cb.data.split(":", 1)[1]
        await set_user_language(cb.from_user.id, lang)
        msg = t("lang_changed", "ru") if lang == "ru" else t("lang_changed_en", "en")
        await cb.message.edit_text(msg)
    except Exception as e:
        logger.exception(f"lang_callback error")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass
