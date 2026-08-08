import logging
import html
import asyncio

from aiogram import F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, InputMediaPhoto

from bot import bot, dp, get_bot_username
from bot.database import (
    get_active_session, clear_active_session,
    get_link_by_code, get_link_by_id,
    get_message_by_id, get_forwarded_message, get_last_forwarded_for_user,
    save_forwarded_message,
    create_message, is_banned, get_or_create_user,
    get_or_create_link, reset_link, set_user_language,
    user_can_see_whois,
    delete_message_row,
    get_forwarded_for_message, delete_forwarded_for_message,
)
from bot.locales import t
from bot.keyboards import stop_session_kb

logger = logging.getLogger(__name__)

# Buffers for incoming photo albums: key = (sender_tg_id, media_group_id)
_album_buffers: dict[tuple, dict] = {}


def _extract_content(message: Message) -> tuple:
    text = message.text or message.caption or ""
    ct = message.content_type
    fid = None
    if message.photo:
        fid = message.photo[-1].file_id
    elif message.document:
        fid = message.document.file_id
    elif message.video:
        fid = message.video.file_id
    elif message.audio:
        fid = message.audio.file_id
    elif message.voice:
        fid = message.voice.file_id
    elif message.sticker:
        fid = message.sticker.file_id
    elif message.animation:
        fid = message.animation.file_id
    elif message.video_note:
        fid = message.video_note.file_id
    return text, ct, fid


def _unsend_kb(lang: str, msg_id: int) -> InlineKeyboardMarkup:
    stop = stop_session_kb(lang).inline_keyboard[0]
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🗑 Удалить у владельца", callback_data=f"unsend:{msg_id}")],
        stop,
    ])


async def _deliver_to_owner(plan: dict) -> list[tuple[int, int]]:
    """Sends anonymous content to the owner. Returns (bot_message_id, owner_tg_id) pairs."""
    owner_tg_id = plan["owner_id"]
    owner_lang = plan["owner_lang"]
    kind = plan["kind"]

    whois_kb = None
    if plan.get("whois"):
        whois_kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=t("whois_btn", owner_lang), callback_data=f"whois:{plan['msg_id']}")],
        ])

    if kind == "text":
        body = t("new_anon", owner_lang).format(text=plan["text"])
        sent = await bot.send_message(owner_tg_id, body, reply_markup=whois_kb)
        return [(sent.message_id, owner_tg_id)]

    if kind == "album":
        media_group = [
            InputMediaPhoto(media=f, caption=(plan.get("text") or "" if i == 0 else None))
            for i, f in enumerate(plan["files"])
        ]
        sent_list = await bot.send_media_group(owner_tg_id, media_group)
        result = [(s.message_id, owner_tg_id) for s in sent_list]
        note = t("new_anon_media", owner_lang).format(text=plan.get("text") or "")
        sent = await bot.send_message(owner_tg_id, note, reply_markup=whois_kb)
        result.append((sent.message_id, owner_tg_id))
        return result

    media_copy = await plan["message_ref"].copy_to(owner_tg_id)
    result = [(media_copy.message_id, owner_tg_id)]
    note = t("new_anon_media", owner_lang).format(text=plan.get("text") or "")
    sent = await bot.send_message(owner_tg_id, note, reply_markup=whois_kb)
    result.append((sent.message_id, owner_tg_id))
    return result


async def _deliver_and_confirm(plan: dict, message_ref: Message | None, reply_to: Message | None = None):
    """Delivers to the owner immediately and shows the sender a 'delete' button."""
    if message_ref is not None:
        plan["message_ref"] = message_ref
    delivered = await _deliver_to_owner(plan)
    for bot_message_id, owner_tg_id in delivered:
        await save_forwarded_message(bot_message_id, owner_tg_id, plan["msg_id"])
    lang = plan.get("sender_lang") or "ru"
    if reply_to is not None:
        await reply_to.answer(t("msg_sent", lang), reply_markup=_unsend_kb(lang, plan["msg_id"]))
    logger.info(
        f"ANON delivered ({plan['kind']}): sender={plan.get('sender_id')} "
        f"-> owner={plan['owner_id']}: {(plan.get('text') or '')[:100]}"
    )


async def _finalize_album(
    key: tuple,
    sender_id: int,
    link,
    owner,
    sender_user,
    username,
    full_name,
):
    """Waits for the album to finish, then delivers it to the owner immediately."""
    await asyncio.sleep(1.3)
    buf = _album_buffers.pop(key, None)
    if not buf or not buf["photos"]:
        return

    files = buf["photos"]
    caption = buf["caption"] or ""
    msg = await create_message(
        link_id=link.id, sender_id=sender_id,
        text=caption, content_type="album", file_id=files[0],
        sender_username=username, sender_full_name=full_name,
    )

    plan = {
        "kind": "album",
        "msg_id": msg.id,
        "text": caption,
        "files": files,
        "owner_id": owner.telegram_id,
        "owner_lang": owner.language or "ru",
        "whois": user_can_see_whois(owner),
        "sender_id": sender_id,
        "sender_lang": sender_user.language or "ru",
    }
    try:
        await _deliver_and_confirm(plan, None, buf["ref"])
    except Exception as e:
        logger.exception(f"ANON album delivery failed msg={msg.id}: {type(e).__name__}: {e}")


@dp.message(~F.reply_to_message)
async def handle_anonymous_message(message: Message, state: FSMContext):
    if message.from_user.id == (await bot.get_me()).id:
        return

    if await state.get_state():
        return

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

    owner = link.user
    sender_user = await get_or_create_user(
        message.from_user.id, message.from_user.username, message.from_user.full_name
    )
    lang = sender_user.language or "ru"

    # ── Album (media group) ──
    if message.media_group_id:
        key = (message.from_user.id, message.media_group_id)
        buf = _album_buffers.get(key)
        if buf is None:
            buf = _album_buffers[key] = {"photos": [], "caption": "", "task": None, "ref": message}
        if message.photo:
            buf["photos"].append(message.photo[-1].file_id)
        if message.caption:
            buf["caption"] = message.caption
        if buf["task"] is None:
            buf["task"] = asyncio.create_task(_finalize_album(
                key, message.from_user.id, link, owner, sender_user,
                message.from_user.username, message.from_user.full_name,
            ))
        return

    # ── Single message ──
    text_content, content_type, file_id = _extract_content(message)
    msg = await create_message(
        link_id=link.id,
        sender_id=message.from_user.id,
        text=text_content,
        content_type=content_type,
        file_id=file_id,
        sender_username=message.from_user.username,
        sender_full_name=message.from_user.full_name,
    )

    plan = {
        "kind": "text" if content_type == "text" else "media",
        "msg_id": msg.id,
        "text": text_content,
        "file_id": file_id,
        "owner_id": owner.telegram_id,
        "owner_lang": owner.language or "ru",
        "whois": user_can_see_whois(owner),
        "sender_id": message.from_user.id,
        "sender_lang": lang,
    }
    try:
        await _deliver_and_confirm(plan, message, message)
    except Exception as e:
        logger.exception(f"ANON delivery failed msg={msg.id}: {type(e).__name__}: {e}")
        try:
            await message.answer("❌ Не удалось доставить сообщение.")
        except Exception:
            pass


@dp.callback_query(F.data.startswith("unsend:"))
async def unsend_callback(cb):
    try:
        await cb.answer()
        msg_id = int(cb.data.split(":")[1])
        msg = await get_message_by_id(msg_id)
        if not msg or msg.sender_id != cb.from_user.id:
            await cb.answer("❌ Сообщение не найдено или уже удалено", show_alert=True)
            return

        forwards = await get_forwarded_for_message(msg_id)
        for fw in forwards:
            try:
                await bot.delete_message(fw.owner_tg_id, fw.bot_message_id)
            except Exception:
                pass
        await delete_forwarded_for_message(msg_id)
        await delete_message_row(msg_id)
        logger.info(f"ANON unsent by sender: msg={msg_id}, copies deleted={len(forwards)}")
        try:
            await cb.message.edit_text("🗑️ <b>Сообщение удалено у владельца.</b>")
        except Exception:
            pass
    except Exception as e:
        logger.exception(f"unsend_callback error")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


@dp.message(F.reply_to_message)
async def handle_reply_to_anonymous(message: Message, state: FSMContext):
    if await state.get_state():
        return

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
    text_content, content_type, file_id = _extract_content(message)

    reply_msg = await create_message(
        link_id=original.link_id,
        sender_id=message.from_user.id,
        text=text_content,
        content_type=content_type,
        file_id=file_id,
        sender_username=message.from_user.username,
        sender_full_name=message.from_user.full_name,
    )

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

    if content_type == "text":
        quote_text = html.escape(original.text or "")
        reply_text = html.escape(text_content)
        body = f"{header}\n\n<blockquote>{quote_text}</blockquote>\n\n{reply_text}"

        if log_dir == "sender->owner" and user_can_see_whois(owner):
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=t("whois_btn", owner.language or "ru"), callback_data=f"whois:{original.id}")],
            ])
            sent = await bot.send_message(recipient_id, body, reply_to_message_id=reply_to, reply_markup=kb)
        else:
            sent = await bot.send_message(recipient_id, body, reply_to_message_id=reply_to)
        await save_forwarded_message(sent.message_id, recipient_id, reply_msg.id)
    else:
        sent = await message.copy_to(recipient_id, reply_to_message_id=reply_to)
        await save_forwarded_message(sent.message_id, recipient_id, reply_msg.id)

        note = f"{header}\n\n{text_content}"
        note_sent = await bot.send_message(recipient_id, note, reply_to_message_id=sent.message_id)
        await save_forwarded_message(note_sent.message_id, recipient_id, reply_msg.id)

    await message.answer(t("reply_sent", lang), reply_markup=stop_session_kb(lang))

    logger.info(
        f"REPLY ({log_dir}): {message.from_user.id} "
        f"(@{message.from_user.username}) -> {recipient_id}: "
        f"{text_content[:100]}"
    )


@dp.callback_query(F.data == "stop_session")
async def stop_session_callback(cb):
    try:
        await cb.answer()
        session = await get_active_session(cb.from_user.id)
        if session:
            await clear_active_session(cb.from_user.id)
        user = await get_or_create_user(cb.from_user.id, cb.from_user.username, cb.from_user.full_name)
        await cb.message.edit_text(t("stopped", user.language or "ru"))
    except Exception as e:
        logger.exception(f"stop_session_callback error")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


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
