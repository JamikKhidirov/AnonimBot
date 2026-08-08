from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp, bot, get_bot_username
from bot.database import (
    get_active_session, clear_active_session,
    get_user_with_links, get_messages_for_link, get_or_create_user,
    reset_link, get_or_create_referral_code, get_link_stats,
    set_custom_greeting,
)
from bot.locales import t
from bot.keyboards import lang_kb


@dp.message(Command("stop"))
async def stop_command(message: Message):
    session = await get_active_session(message.from_user.id)
    if not session:
        user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
        await message.answer(t("no_session", user.language or "ru"))
        return
    await clear_active_session(message.from_user.id)
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(t("stopped", user.language or "ru"))


@dp.message(Command("messages"))
async def messages_command(message: Message):
    user = await get_user_with_links(message.from_user.id)
    lang = user.language if user else "ru"
    if not user:
        await message.answer(t("no_session", lang))
        return
    if not user.links:
        await message.answer(t("no_messages", lang))
        return

    link = user.links[0]
    msgs = await get_messages_for_link(link.id)
    if not msgs:
        await message.answer(t("no_messages", lang))
        return

    text_lines = [t("your_messages", lang).format(count=len(msgs))]
    for m in msgs[:10]:
        text_lines.append(
            f"─ {m.created_at.strftime('%d.%m %H:%M')}\n"
            f"  {m.text[:200]}\n"
        )
    if len(msgs) > 10:
        text_lines.append(f"\n... и ещё {len(msgs) - 10}")

    ref_code = await get_or_create_referral_code(message.from_user.id)
    ref_url = f"https://t.me/{get_bot_username()}?start={ref_code}"

    from datetime import datetime
    bonus_text = ""
    if user.referral_bonus_until and user.referral_bonus_until > datetime.utcnow():
        remaining = (user.referral_bonus_until - datetime.utcnow()).days
        hours = ((user.referral_bonus_until - datetime.utcnow()).seconds // 3600)
        bonus_text = f"\n👁 <b>Просмотр отправителей:</b> ещё {remaining}д {hours}ч\n"

    text_lines.append(f"\n{bonus_text}━━━━━━━━━━━━━━━\n👥 <b>Реферальная ссылка:</b>\n<code>{ref_url}</code>")

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📈 Статистика", callback_data="link_stats"),
         InlineKeyboardButton(text=t("reset_link_btn", lang), callback_data="reset_link")],
        [InlineKeyboardButton(text=t("lang_btn_ru" if lang == "ru" else "lang_btn_en", lang), callback_data=f"lang:{'en' if lang == 'ru' else 'ru'}")],
    ])
    await message.answer("\n".join(text_lines), reply_markup=kb)


@dp.callback_query(lambda c: c.data == "link_stats")
async def link_stats_callback(cb):
    try:
        await cb.answer()
        user = await get_user_with_links(cb.from_user.id)
        lang = user.language if user else "ru"
        if not user or not user.links:
            await cb.message.edit_text(t("no_messages", lang), reply_markup=lang_kb())
            return
        link = user.links[0]
        stats = await get_link_stats(link.id)
        daily = stats["daily"]
        days_text = ""
        if daily:
            lines = []
            for day, count in daily:
                d = day[5:].replace("-", ".")
                bar = "█" * min(count, 10)
                lines.append(f"  📅 {d}: <b>{count}</b> {bar}")
            days_text = "\n".join(lines)
        else:
            days_text = "  пока нет сообщений"
        text = (
            f"📈 <b>Статистика твоей ссылки</b>\n\n"
            f"👁 Открытий ссылки: <b>{stats['views']}</b>\n"
            f"💬 Всего сообщений: <b>{stats['total']}</b>\n\n"
            f"📊 <b>По дням:</b>\n{days_text}"
        )
        from bot.keyboards import back_kb
        await cb.message.edit_text(text, reply_markup=back_kb("start"))
    except Exception as e:
        import logging
        logging.exception(f"link_stats_callback error")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass


@dp.message(Command("stats"))
async def stats_command(message: Message):
    user = await get_user_with_links(message.from_user.id)
    lang = user.language if user else "ru"
    if not user or not user.links:
        await message.answer(t("no_messages", lang))
        return
    link = user.links[0]
    stats = await get_link_stats(link.id)
    daily = stats["daily"]
    if daily:
        lines = [f"  📅 {d[5:].replace('-', '.')}: <b>{c}</b> " + "█" * min(c, 10) for d, c in daily]
        days_text = "\n".join(lines)
    else:
        days_text = "  пока нет сообщений"
    await message.answer(
        f"📈 <b>Статистика твоей ссылки</b>\n\n"
        f"👁 Открытий: <b>{stats['views']}</b>\n"
        f"💬 Сообщений: <b>{stats['total']}</b>\n\n"
        f"📊 <b>По дням:</b>\n{days_text}"
    )


@dp.message(Command("setgreeting"))
async def set_greeting_command(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    lang = user.language or "ru"
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer(
            "💬 <b>Приветствие для анонимов</b>\n\n"
            "Эту фразу увидит человек, который откроет твою ссылку (вместо стандартного «Пиши анонимно!»).\n\n"
            f"Установить:\n<code>/setgreeting Привет! Пиши мне анонимно 🤫</code>\n\n"
            f"Сбросить:\n<code>/setgreeting -</code>"
        )
        return
    text = args[1].strip()
    if text == "-":
        text = None
        await set_custom_greeting(message.from_user.id, None)
        await message.answer("✅ Приветствие сброшено.")
    else:
        await set_custom_greeting(message.from_user.id, text)
        await message.answer(f"✅ Приветствие сохранено:\n\n{text}")


@dp.message(Command("help"))
async def help_command(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    lang = user.language or "ru"
    await message.answer(t("help_text", lang))


@dp.message(Command("language"))
async def language_command(message: Message):
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(t("lang_choose", user.language or "ru"), reply_markup=lang_kb())


@dp.message(Command("resetlink"))
async def resetlink_command(message: Message):
    from bot.keyboards import reset_link_kb
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    lang = user.language or "ru"
    await message.answer(t("reset_link_confirm", lang), reply_markup=reset_link_kb())
