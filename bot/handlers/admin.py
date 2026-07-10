import logging
import asyncio
import io

from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile
from aiogram.exceptions import TelegramBadRequest

from bot import bot, dp, get_bot_username
from bot.config import DEVELOPER_ID
from bot.database import (
    get_user, get_user_with_links, get_all_users,
    search_users, set_admin, get_all_admin_records,
    get_message_count, get_user_count, get_link_count,
    get_all_messages, get_message_by_id, search_messages,
    get_messages_by_sender_id, get_sender_message_count,
    get_messages_for_link, get_link_by_id, get_forwarded_message,
    ban_user, unban_user, is_banned, get_all_banned,
    get_all_user_ids, export_messages_csv, delete_old_messages,
    get_or_create_user,
)
from bot.locales import t, role_label
from bot.keyboards import (
    admin_menu_kb, back_kb,
    msgs_page_kb, msg_info_kb, sender_msgs_page_kb,
    admin_search_kb, admin_admins_kb,
)

logger = logging.getLogger(__name__)


def is_dev(tg_id: int) -> bool:
    return tg_id == DEVELOPER_ID


async def ensure_admin(tg_id: int) -> bool:
    u = await get_user(tg_id)
    return u is not None and u.is_admin


def _fmt_user(u, lang: str = "ru") -> str:
    role = role_label(lang, u.is_developer, u.is_admin)
    name = f"@{u.username}" if u.username else u.full_name or f"ID {u.telegram_id}"
    return f"{role} | {name} | <code>{u.telegram_id}</code>"


async def _user_lang(tg_id: int) -> str:
    u = await get_user(tg_id)
    return u.language if u else "ru"


# ───────────────────────────── /admin ─────────────────────────────

@dp.message(Command("admin"))
async def admin_command(message: Message):
    if not await ensure_admin(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    await message.answer(t("admin_panel", await _user_lang(message.from_user.id)), reply_markup=admin_menu_kb())


# ─────────────────────── admin callbacks ───────────────────────

@dp.callback_query(F.data.startswith("admin_"))
async def admin_callback(cb: CallbackQuery):
    try:
        if not await ensure_admin(cb.from_user.id):
            await cb.answer(t("access_denied", await _user_lang(cb.from_user.id)), show_alert=True)
            return
        await cb.answer()
        data = cb.data
        lang = await _user_lang(cb.from_user.id)

        if data == "admin_panel":
            await cb.message.edit_text(t("admin_panel", lang), reply_markup=admin_menu_kb())
            return

        if data == "admin_stats":
            mc = await get_message_count()
            uc = await get_user_count()
            lc = await get_link_count()
            await cb.message.edit_text(
                t("stats", lang).format(users=uc, links=lc, msgs=mc),
                reply_markup=back_kb(),
            )
            return

        if data == "admin_users":
            users = await get_all_users()
            lines = [t("all_users", lang).format(count=len(users))]
            for u in users:
                lines.append(_fmt_user(u, lang))
                if len(lines) > 60:
                    lines.append(f"... и ещё {len(users) - 60}")
                    break
            await cb.message.edit_text("\n".join(lines), reply_markup=back_kb())
            return

        if data == "admin_admins":
            await cb.message.edit_text(
                t("admin_mgmt", lang),
                reply_markup=admin_admins_kb(),
            )
            return

        if data == "admin_admins_list":
            admins = await get_all_admin_records()
            if not admins:
                await cb.message.edit_text(t("no_admins", lang), reply_markup=back_kb())
                return
            lines = [t("admins_list", lang).format(count=len(admins))]
            for a in admins:
                user = await get_user(a.telegram_id)
                name = f"@{user.username}" if user and user.username else (user.full_name if user else f"ID {a.telegram_id}")
                added_by = await get_user(a.added_by)
                added_name = f"@{added_by.username}" if added_by and added_by.username else str(a.added_by)
                lines.append(
                    f"👑 {name} — <code>{a.telegram_id}</code>\n"
                    f"   Назначен: {a.created_at.strftime('%d.%m.%Y')} by {added_name}"
                )
            await cb.message.edit_text("\n".join(lines), reply_markup=back_kb())
            return

        if data == "admin_add_admin":
            await cb.message.edit_text(
                "📝 <b>Добавление администратора</b>\n\n"
                "Отправь команду:\n<code>/add_admin [user_id]</code>",
                reply_markup=back_kb(),
            )
            return

        if data == "admin_remove_admin":
            await cb.message.edit_text(
                "📝 <b>Удаление администратора</b>\n\n"
                "Отправь команду:\n<code>/remove_admin [user_id]</code>",
                reply_markup=back_kb(),
            )
            return

        if data == "admin_search":
            await cb.message.edit_text(
                t("search_subtitle", lang),
                reply_markup=admin_search_kb(),
            )
            return

        if data == "admin_search_user":
            await cb.message.edit_text(t("search_user_title", lang), reply_markup=back_kb())
            return

        if data == "admin_search_msgs":
            await cb.message.edit_text(t("search_msgs_title", lang), reply_markup=back_kb())
            return

        if data == "admin_view_user":
            await cb.message.edit_text(t("view_user_title", lang), reply_markup=back_kb())
            return

        if data == "admin_view_msgs":
            await cb.message.edit_text(t("view_msgs_title", lang), reply_markup=back_kb())
            return

        if data == "admin_sender":
            await cb.message.edit_text(t("sender_title", lang), reply_markup=back_kb())
            return

        if data == "admin_tools":
            from bot.keyboards import admin_tools_kb
            await cb.message.edit_text(
                "🛠 <b>Инструменты</b>\n\nВыбери действие:",
                reply_markup=admin_tools_kb(),
            )
            return

        if data == "admin_ban_menu":
            await cb.message.edit_text(
                "⛔ <b>Бан / Разбан</b>\n\n"
                "<code>/ban [user_id] [причина]</code> — заблокировать\n"
                "<code>/unban [user_id]</code> — разблокировать",
                reply_markup=back_kb(),
            )
            return

        if data == "admin_banlist":
            banned = await get_all_banned()
            if not banned:
                await cb.message.edit_text(t("no_banned", lang), reply_markup=back_kb())
                return
            lines = [t("ban_list_title", lang).format(count=len(banned))]
            for b in banned:
                by_user = await get_user(b.banned_by)
                by_name = f"@{by_user.username}" if by_user else str(b.banned_by)
                lines.append(
                    f"\n<code>{b.telegram_id}</code>\n"
                    f"  {t('ban_reason', lang).format(reason=b.reason or '-')}\n"
                    f"  {t('ban_date', lang).format(date=b.created_at.strftime('%d.%m.%Y'))}\n"
                    f"  {t('ban_by', lang).format(by=by_name)}"
                )
            await cb.message.edit_text("\n".join(lines), reply_markup=back_kb())
            return

        if data == "admin_broadcast":
            await cb.message.edit_text(
                "📢 <b>Рассылка</b>\n\n"
                "Отправь команду:\n<code>/broadcast [текст]</code>\n\n"
                "Сообщение будет отправлено всем пользователям бота.",
                reply_markup=back_kb(),
            )
            return

        if data == "admin_cleanup":
            await cb.message.edit_text(
                "🧹 <b>Очистка старых сообщений</b>\n\n"
                "Отправь команду:\n<code>/cleanup [дни]</code>\n\n"
                "Например: /cleanup 30 — удалит все сообщения старше 30 дней.",
                reply_markup=back_kb(),
            )
            return

        if data == "admin_export_csv":
            await cb.message.edit_text(
                "📤 <b>Экспорт сообщений</b>\n\n"
                "Отправь команду:\n<code>/export_csv</code>\n\n"
                "Бот пришлёт файл .csv со всеми сообщениями.",
                reply_markup=back_kb(),
            )
            return

        if data == "admin_reset_link_tool":
            await cb.message.edit_text(
                "🔄 <b>Сброс ссылки</b>\n\n"
                "Отправь команду:\n<code>/resetlink</code>\n\n"
                "Твоя текущая ссылка станет неактивной, создастся новая.",
                reply_markup=back_kb(),
            )
            return

        if data.startswith("admin_msgs:"):
            page = int(data.split(":", 1)[1])
            msgs, total = await get_all_messages(page, 5)
            if not msgs:
                await cb.message.edit_text(t("no_msgs_yet", lang), reply_markup=back_kb())
                return

            lines = [t("all_msgs_title", lang).format(page=page + 1)]
            for i, m in enumerate(msgs, 1):
                sender = m.sender_full_name or f"Пользователь {m.sender_id}"
                lines.append(
                    f"\n{i}. #{m.id}\n"
                    f"   От: {sender}\n"
                    f"   Текст: {m.text[:150]}"
                )
            await cb.message.edit_text(
                "\n".join(lines),
                reply_markup=msgs_page_kb(msgs, page, total),
            )
            return

        if data == "admin_dev":
            if not is_dev(cb.from_user.id):
                await cb.message.edit_text(t("dev_only", lang), reply_markup=back_kb())
                return
            await cb.message.edit_text(t("dev_panel", lang), reply_markup=back_kb())
            return

    except Exception as e:
        logger.exception(f"admin_callback error: data={cb.data}")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}", reply_markup=back_kb())
        except Exception:
            pass

    if data == "admin_panel":
        await cb.message.edit_text(t("admin_panel", lang), reply_markup=admin_menu_kb())
        return

    if data == "admin_stats":
        mc = await get_message_count()
        uc = await get_user_count()
        lc = await get_link_count()
        await cb.message.edit_text(
            t("stats", lang).format(users=uc, links=lc, msgs=mc),
            reply_markup=back_kb(),
        )
        return

    if data == "admin_users":
        users = await get_all_users()
        lines = [t("all_users", lang).format(count=len(users))]
        for u in users:
            lines.append(_fmt_user(u, lang))
            if len(lines) > 60:
                lines.append(f"... и ещё {len(users) - 60}")
                break
        await cb.message.edit_text("\n".join(lines), reply_markup=back_kb())
        return

    if data == "admin_admins":
        await cb.message.edit_text(
            t("admin_mgmt", lang),
            reply_markup=admin_admins_kb(),
        )
        return

    if data == "admin_admins_list":
        admins = await get_all_admin_records()
        if not admins:
            await cb.message.edit_text(t("no_admins", lang), reply_markup=back_kb())
            return
        lines = [t("admins_list", lang).format(count=len(admins))]
        for a in admins:
            user = await get_user(a.telegram_id)
            name = f"@{user.username}" if user and user.username else (user.full_name if user else f"ID {a.telegram_id}")
            added_by = await get_user(a.added_by)
            added_name = f"@{added_by.username}" if added_by and added_by.username else str(a.added_by)
            lines.append(
                f"👑 {name} — <code>{a.telegram_id}</code>\n"
                f"   Назначен: {a.created_at.strftime('%d.%m.%Y')} by {added_name}"
            )
        await cb.message.edit_text("\n".join(lines), reply_markup=back_kb())
        return

    if data == "admin_add_admin":
        await cb.message.edit_text(
            "📝 <b>Добавление администратора</b>\n\n"
            "Отправь команду:\n<code>/add_admin [user_id]</code>",
            reply_markup=back_kb(),
        )
        return

    if data == "admin_remove_admin":
        await cb.message.edit_text(
            "📝 <b>Удаление администратора</b>\n\n"
            "Отправь команду:\n<code>/remove_admin [user_id]</code>",
            reply_markup=back_kb(),
        )
        return

    if data == "admin_search":
        await cb.message.edit_text(
            t("search_subtitle", lang),
            reply_markup=admin_search_kb(),
        )
        return

    if data == "admin_search_user":
        await cb.message.edit_text(t("search_user_title", lang), reply_markup=back_kb())
        return

    if data == "admin_search_msgs":
        await cb.message.edit_text(t("search_msgs_title", lang), reply_markup=back_kb())
        return

    if data == "admin_view_user":
        await cb.message.edit_text(t("view_user_title", lang), reply_markup=back_kb())
        return

    if data == "admin_view_msgs":
        await cb.message.edit_text(t("view_msgs_title", lang), reply_markup=back_kb())
        return

    if data == "admin_sender":
        await cb.message.edit_text(t("sender_title", lang), reply_markup=back_kb())
        return

    if data.startswith("admin_msgs:"):
        page = int(data.split(":", 1)[1])
        msgs, total = await get_all_messages(page, 5)
        if not msgs:
            await cb.message.edit_text(t("no_msgs_yet", lang), reply_markup=back_kb())
            return

        lines = [t("all_msgs_title", lang).format(page=page + 1)]
        for i, m in enumerate(msgs, 1):
            sender = m.sender_full_name or f"Пользователь {m.sender_id}"
            lines.append(
                f"\n{i}. #{m.id}\n"
                f"   От: {sender}\n"
                f"   Текст: {m.text[:150]}"
            )
        await cb.message.edit_text(
            "\n".join(lines),
            reply_markup=msgs_page_kb(msgs, page, total),
        )
        return

    if data == "admin_dev":
        if not is_dev(cb.from_user.id):
            await cb.message.edit_text(t("dev_only", lang), reply_markup=back_kb())
            return
        await cb.message.edit_text(t("dev_panel", lang), reply_markup=back_kb())
        return


# ──────────────────────── msg_info callback ────────────────────────

@dp.callback_query(F.data.startswith("msg_info:"))
async def msg_info_callback(cb: CallbackQuery):
    try:
        if not await ensure_admin(cb.from_user.id):
            await cb.answer(t("access_denied", await _user_lang(cb.from_user.id)), show_alert=True)
            return
        await cb.answer()
        lang = await _user_lang(cb.from_user.id)

        msg_id = int(cb.data.split(":", 1)[1])
        msg = await get_message_by_id(msg_id)
        if not msg:
            await cb.message.edit_text(t("not_found", lang), reply_markup=back_kb())
            return

        link = await get_link_by_id(msg.link_id)
        owner_info = (
            f"ID: <code>{link.user.telegram_id}</code> (@{link.user.username})"
            if link and link.user else "?"
        )

        sender_msgs_count = await get_sender_message_count(msg.sender_id)

        text = (
            f"{t('msg_info_title', lang).format(id=msg.id)}\n\n"
            f"{t('msg_sender', lang)}\n"
            f"  ID: <code>{msg.sender_id}</code>\n"
            f"  Username: @{msg.sender_username or 'N/A'}\n"
            f"  Имя: {msg.sender_full_name or 'N/A'}\n"
            f"  {t('msg_total', lang).format(count=sender_msgs_count)}\n\n"
            f"{t('msg_link_owner', lang)} {owner_info}\n\n"
            f"{t('msg_text', lang)}\n{msg.text}\n\n"
            f"{t('msg_time', lang)} {msg.created_at.strftime('%d.%m.%Y %H:%M:%S')}"
        )

        await cb.message.edit_text(text, reply_markup=msg_info_kb(msg.id, msg.sender_id))
    except Exception as e:
        logger.exception(f"msg_info_callback error: data={cb.data}")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}", reply_markup=back_kb())
        except Exception:
            pass


# ──────────────────── sender_msgs callback ────────────────────

@dp.callback_query(F.data.startswith("sender_msgs:"))
async def sender_msgs_callback(cb: CallbackQuery):
    try:
        if not await ensure_admin(cb.from_user.id):
            await cb.answer(t("access_denied", await _user_lang(cb.from_user.id)), show_alert=True)
            return
        await cb.answer()
        lang = await _user_lang(cb.from_user.id)

        parts = cb.data.split(":")
        sender_tg_id = int(parts[1])
        page = int(parts[2])
        msgs, total = await get_messages_by_sender_id(sender_tg_id, page, 5)

        if not msgs:
            await cb.message.edit_text(
                t("no_msgs_from_sender", lang).format(id=sender_tg_id),
                reply_markup=back_kb(),
            )
            return

        lines = [t("msgs_from_sender", lang).format(id=sender_tg_id, page=page + 1)]
        for i, m in enumerate(msgs, 1):
            link_obj = await get_link_by_id(m.link_id)
            target = f"@{link_obj.user.username}" if link_obj and link_obj.user else f"владелец #{m.link_id}"
            lines.append(f"\n{i}. #{m.id} → <b>{target}</b>\n"
                         f"   📅 {m.created_at.strftime('%d.%m.%Y %H:%M')}\n"
                         f"   💬 {m.text[:200]}")

        await cb.message.edit_text(
            "\n".join(lines),
            reply_markup=sender_msgs_page_kb(sender_tg_id, msgs, page, total),
        )
    except Exception as e:
        logger.exception(f"sender_msgs_callback error: data={cb.data}")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}", reply_markup=back_kb())
        except Exception:
            pass


# ──────────────────── view_user callback ────────────────────

@dp.callback_query(F.data.startswith("view_user:"))
async def view_user_callback(cb: CallbackQuery):
    try:
        if not await ensure_admin(cb.from_user.id):
            await cb.answer(t("access_denied", await _user_lang(cb.from_user.id)), show_alert=True)
            return
        await cb.answer()
        lang = await _user_lang(cb.from_user.id)

        tg_id = int(cb.data.split(":", 1)[1])
        user = await get_user(tg_id)
        if not user:
            await cb.message.edit_text(t("user_not_found", lang).format(id=tg_id), reply_markup=back_kb())
            return

        role = role_label(lang, user.is_developer, user.is_admin)
        await cb.message.edit_text(
            f"{t('user_info_title', lang)}\n\n"
            f"ID: <code>{user.telegram_id}</code>\n"
            f"{t('username_label', lang).format(name=user.username or 'N/A')}\n"
            f"{t('name_label', lang).format(name=user.full_name or 'N/A')}\n"
            f"{t('role_label', lang).format(role=role)}\n"
            f"{t('reg_date', lang).format(date=user.created_at.strftime('%d.%m.%Y %H:%M'))}",
            reply_markup=back_kb(),
        )
    except Exception as e:
        logger.exception(f"view_user_callback error: data={cb.data}")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}", reply_markup=back_kb())
        except Exception:
            pass


# ────────────────────── whois callback ──────────────────────

@dp.callback_query(F.data.startswith("whois:"))
async def whois_callback(cb: CallbackQuery):
    try:
        if not await ensure_admin(cb.from_user.id):
            await cb.answer(t("access_denied", await _user_lang(cb.from_user.id)), show_alert=True)
            return
        await cb.answer()
        lang = await _user_lang(cb.from_user.id)

        msg_id = int(cb.data.split(":", 1)[1])
        msg = await get_message_by_id(msg_id)
        if not msg:
            await cb.message.edit_text(t("not_found", lang), reply_markup=back_kb())
            return

        sender_id = msg.sender_id
        total_from_sender = await get_sender_message_count(sender_id)
        recent_msgs, _ = await get_messages_by_sender_id(sender_id, 0, 5)

        text = (
            f"{t('whois_title', lang)}\n\n"
            f"ID: <code>{sender_id}</code>\n"
            f"Username: @{msg.sender_username or 'N/A'}\n"
            f"Имя: {msg.sender_full_name or 'N/A'}\n"
            f"{t('whois_total', lang).format(count=total_from_sender)}\n"
            f"{t('whois_time', lang).format(time=msg.created_at.strftime('%d.%m.%Y %H:%M:%S'))}\n\n"
            f"{t('whois_text', lang)} {msg.text}"
        )

        if recent_msgs:
            text += t("whois_recent", lang)
            for i, m in enumerate(recent_msgs[:5], 1):
                link_obj = await get_link_by_id(m.link_id)
                target = f"@{link_obj.user.username}" if link_obj and link_obj.user else f"ID {m.link_id}"
                text += (
                    f"\n{i}. #{m.id} → <b>{target}</b>\n"
                    f"   {m.created_at.strftime('%d.%m %H:%M')} — {m.text[:100]}"
                )

        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(
                text=t("whois_all_btn", lang),
                callback_data=f"sender_msgs:{sender_id}:0",
            )],
            [InlineKeyboardButton(
                text=t("whois_profile_btn", lang),
                callback_data=f"view_user:{sender_id}",
            )],
        ])

        await cb.message.edit_text(text, reply_markup=kb)
    except Exception as e:
        logger.exception(f"whois_callback error: data={cb.data}")
        try:
            await cb.message.edit_text(f"❌ Ошибка: {e}", reply_markup=back_kb())
        except Exception:
            pass


# ────────────────────── noop callback ──────────────────────

@dp.callback_query(F.data == "noop")
async def noop_callback(cb: CallbackQuery):
    await cb.answer()


# ═══════════════════════ COMMANDS ═══════════════════════

@dp.message(Command("add_admin"))
async def add_admin_command(message: Message):
    if not is_dev(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer(t("add_admin_usage", "ru"))
        return
    target_id = int(args[1].strip())
    user = await get_user(target_id)
    if not user:
        await message.answer(t("user_not_found", "ru").format(id=target_id))
        return
    await set_admin(target_id, True, message.from_user.id)
    await message.answer(t("add_admin_done", "ru").format(id=target_id))
    try:
        await bot.send_message(target_id, t("add_admin_notified", user.language or "ru"))
    except Exception:
        pass


@dp.message(Command("remove_admin"))
async def remove_admin_command(message: Message):
    if not is_dev(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer(t("remove_admin_usage", "ru"))
        return
    target_id = int(args[1].strip())
    if target_id == DEVELOPER_ID:
        await message.answer(t("remove_admin_cant", "ru"))
        return
    user = await get_user(target_id)
    if not user:
        await message.answer(t("remove_admin_not_found", "ru").format(id=target_id))
        return
    await set_admin(target_id, False)
    await message.answer(t("remove_admin_done", "ru").format(id=target_id))


@dp.message(Command("view_user"))
async def view_user_command(message: Message):
    if not await ensure_admin(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    lang = await _user_lang(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer(t("view_user_usage", lang))
        return
    target_id = int(args[1].strip())
    user = await get_user(target_id)
    if not user:
        await message.answer(t("user_not_found", lang).format(id=target_id))
        return

    role = role_label(lang, user.is_developer, user.is_admin)
    await message.answer(
        f"{t('user_info_title', lang)}\n\n"
        f"ID: <code>{user.telegram_id}</code>\n"
        f"{t('username_label', lang).format(name=user.username or 'N/A')}\n"
        f"{t('name_label', lang).format(name=user.full_name or 'N/A')}\n"
        f"{t('role_label', lang).format(role=role)}\n"
        f"{t('reg_date', lang).format(date=user.created_at.strftime('%d.%m.%Y %H:%M'))}"
    )


@dp.message(Command("view_messages"))
async def view_messages_command(message: Message):
    if not await ensure_admin(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    lang = await _user_lang(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer(t("view_messages_usage", lang))
        return
    target_id = int(args[1].strip())
    user = await get_user_with_links(target_id)
    if not user:
        await message.answer(t("user_not_found", lang).format(id=target_id))
        return
    if not user.links:
        await message.answer(t("no_links", lang).format(id=target_id))
        return

    link = user.links[0]
    msgs = await get_messages_for_link(link.id)
    if not msgs:
        await message.answer(t("no_msgs_for_user", lang).format(id=target_id))
        return

    lines = [f"<b>Сообщения для пользователя <code>{target_id}</code> ({len(msgs)}):</b>\n"]
    for m in msgs:
        sender = f"@{m.sender_username}" if m.sender_username else m.sender_full_name or f"Пользователь {m.sender_id}"
        lines.append(
            f"\n─ <b>От:</b> {sender} (<code>{m.sender_id}</code>)\n"
            f"  <b>ID:</b> #{m.id}\n"
            f"  <b>Текст:</b> {m.text}"
        )
    for chunk in _chunkify(lines, 20):
        await message.answer("\n".join(chunk))


@dp.message(Command("sender"))
async def sender_command(message: Message):
    if not await ensure_admin(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    lang = await _user_lang(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer(t("sender_usage", lang))
        return

    msg_id = int(args[1].strip())
    msg = await get_message_by_id(msg_id)
    if not msg:
        await message.answer(t("msg_not_found", lang).format(id=msg_id))
        return

    link = await get_link_by_id(msg.link_id)
    owner_info = f"<code>{link.user.telegram_id}</code>" if link and link.user else "?"

    sender_msgs_count = await get_sender_message_count(msg.sender_id)

    await message.answer(
        f"{t('msg_info_title', lang).format(id=msg.id)}\n\n"
        f"{t('msg_sender', lang)}\n"
        f"  ID: <code>{msg.sender_id}</code>\n"
        f"  Username: @{msg.sender_username or 'N/A'}\n"
        f"  Имя: {msg.sender_full_name or 'N/A'}\n"
        f"  {t('msg_total', lang).format(count=sender_msgs_count)}\n\n"
        f"{t('msg_link_owner', lang)} {owner_info}\n\n"
        f"{t('msg_text', lang)}\n{msg.text}\n\n"
        f"{t('msg_time', lang)} {msg.created_at.strftime('%d.%m.%Y %H:%M:%S')}"
    )


@dp.message(Command("search_user"))
async def search_user_command(message: Message):
    if not await ensure_admin(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    lang = await _user_lang(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer(t("search_user_usage", lang))
        return

    query = args[1].strip()
    users = await search_users(query)
    if not users:
        await message.answer(t("no_users_found", lang))
        return

    lines = [t("search_results_users", lang).format(query=query, count=len(users))]
    for u in users:
        lines.append(_fmt_user(u, lang))
        if len(lines) > 30:
            lines.append(f"\n... и ещё {len(users) - 30}")
            break
    await message.answer("\n".join(lines))


@dp.message(Command("search_messages"))
async def search_messages_command(message: Message):
    if not await ensure_admin(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    lang = await _user_lang(message.from_user.id)
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer(t("search_msgs_usage", lang))
        return

    query = args[1].strip()
    msgs = await search_messages(query)
    if not msgs:
        await message.answer(t("no_msgs_found", lang))
        return

    lines = [t("search_results_msgs", lang).format(query=query, count=len(msgs))]
    for m in msgs[:15]:
        sender = m.sender_full_name or f"Пользователь {m.sender_id}"
        lines.append(
            f"\n#{m.id} от {sender} (<code>{m.sender_id}</code>):\n"
            f"  {m.text[:150]}"
        )
    if len(msgs) > 15:
        lines.append(f"\n... и ещё {len(msgs) - 15}")
    await message.answer("\n".join(lines))


def _chunkify(lines: list[str], size: int) -> list[list[str]]:
    return [lines[i:i + size] for i in range(0, len(lines), size)]


@dp.message(Command("show"))
async def show_command(message: Message):
    if not await ensure_admin(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    lang = await _user_lang(message.from_user.id)

    replied = message.reply_to_message
    if not replied or replied.from_user.id != bot.id:
        await message.answer(t("show_usage", lang))
        return

    forwarded = await get_forwarded_message(replied.message_id, message.from_user.id)
    if not forwarded:
        await message.answer(t("not_anon_msg", lang))
        return

    original = await get_message_by_id(forwarded.original_msg_id)
    if not original:
        await message.answer(t("original_not_found", lang))
        return

    total = await get_sender_message_count(original.sender_id)
    text = (
        f"{t('show_title', lang)}\n\n"
        f"ID: <code>{original.sender_id}</code>\n"
        f"Username: @{original.sender_username or 'N/A'}\n"
        f"Имя: {original.sender_full_name or 'N/A'}\n"
        f"{t('show_total', lang).format(count=total)}\n"
        f"{t('whois_text', lang)} {original.text}"
    )
    await message.answer(text)


# ═══════════════════════ NEW COMMANDS ═══════════════════════

@dp.message(Command("ban"))
async def ban_command(message: Message):
    if not is_dev(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    args = message.text.split(maxsplit=2)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer(t("ban_usage", "ru"))
        return
    target_id = int(args[1].strip())
    reason = args[2].strip() if len(args) > 2 else None

    if await is_banned(target_id):
        await message.answer(t("ban_already", "ru").format(id=target_id))
        return
    await ban_user(target_id, message.from_user.id, reason)
    await message.answer(t("ban_done", "ru").format(id=target_id, reason=reason or "-"))


@dp.message(Command("unban"))
async def unban_command(message: Message):
    if not is_dev(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer(t("unban_usage", "ru"))
        return
    target_id = int(args[1].strip())

    if not await is_banned(target_id):
        await message.answer(t("unban_not_found", "ru").format(id=target_id))
        return
    await unban_user(target_id)
    await message.answer(t("unban_done", "ru").format(id=target_id))


@dp.message(Command("banlist"))
async def banlist_command(message: Message):
    if not await ensure_admin(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    lang = await _user_lang(message.from_user.id)
    banned = await get_all_banned()
    if not banned:
        await message.answer(t("no_banned", lang))
        return

    lines = [t("ban_list_title", lang).format(count=len(banned))]
    for b in banned:
        by_user = await get_user(b.banned_by)
        by_name = f"@{by_user.username}" if by_user else str(b.banned_by)
        lines.append(
            f"\n<code>{b.telegram_id}</code>\n"
            f"  {t('ban_reason', lang).format(reason=b.reason or '-')}\n"
            f"  {t('ban_date', lang).format(date=b.created_at.strftime('%d.%m.%Y'))}\n"
            f"  {t('ban_by', lang).format(by=by_name)}"
        )
    await message.answer("\n".join(lines))


@dp.message(Command("broadcast"))
async def broadcast_command(message: Message):
    if not is_dev(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip():
        await message.answer(t("broadcast_usage", "ru"))
        return

    text = args[1].strip()
    user_ids = await get_all_user_ids()
    await message.answer(t("broadcast_start", "ru").format(count=len(user_ids)))

    sent = 0
    errors = 0
    for uid in user_ids:
        if uid == message.from_user.id:
            continue
        try:
            user = await get_user(uid)
            preview = t("broadcast_preview", user.language if user else "ru").format(text=text)
            await bot.send_message(uid, preview)
            sent += 1
        except Exception:
            errors += 1
        await asyncio.sleep(0.05)

    await message.answer(t("broadcast_done", "ru").format(sent=sent, errors=errors))


@dp.message(Command("export_csv"))
async def export_csv_command(message: Message):
    if not is_dev(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    await message.answer(t("export_start", "ru"))
    try:
        csv_data = await export_messages_csv()
        await message.answer_document(
            InputFile(io.BytesIO(csv_data.encode()), filename="messages.csv"),
            caption="📤 Экспорт сообщений",
        )
    except Exception as e:
        logger.error(f"CSV export error: {e}")
        await message.answer(t("export_error", "ru"))


@dp.message(Command("cleanup"))
async def cleanup_command(message: Message):
    if not is_dev(message.from_user.id):
        await message.answer(t("access_denied", await _user_lang(message.from_user.id)))
        return
    args = message.text.split(maxsplit=1)
    if len(args) < 2 or not args[1].strip().isdigit():
        await message.answer(t("cleanup_usage", "ru"))
        return
    days = int(args[1].strip())
    count = await delete_old_messages(days)
    await message.answer(t("cleanup_done", "ru").format(count=count))


@dp.message(Command("language"))
async def language_command(message: Message):
    from bot.keyboards import lang_kb
    user = await get_or_create_user(message.from_user.id, message.from_user.username, message.from_user.full_name)
    await message.answer(t("lang_choose", user.language or "ru"), reply_markup=lang_kb())
