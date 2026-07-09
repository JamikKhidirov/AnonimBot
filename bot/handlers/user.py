from aiogram.filters import Command
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton

from bot import dp, bot, get_bot_username
from bot.database import (
    get_active_session, clear_active_session,
    get_user_with_links, get_messages_for_link, get_or_create_user,
    reset_link,
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

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("reset_link_btn", lang), callback_data="reset_link")],
        [InlineKeyboardButton(text=t("lang_btn_ru" if lang == "ru" else "lang_btn_en", lang), callback_data=f"lang:{'en' if lang == 'ru' else 'ru'}")],
    ])
    await message.answer("\n".join(text_lines), reply_markup=kb)


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
