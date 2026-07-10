from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="✉️ Сообщения", callback_data="admin_msgs:0"),
         InlineKeyboardButton(text="👑 Админы", callback_data="admin_admins")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search"),
         InlineKeyboardButton(text="🛠 Инструменты", callback_data="admin_tools")],
        [InlineKeyboardButton(text="⚙️ Для разработчика", callback_data="admin_dev")],
    ])


def back_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀ Назад в админку", callback_data="admin_panel")],
    ])


def admin_search_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔍 Поиск пользователя", callback_data="admin_search_user"),
         InlineKeyboardButton(text="🔍 Поиск сообщений", callback_data="admin_search_msgs")],
        [InlineKeyboardButton(text="👤 Инфо о пользователе по ID", callback_data="admin_view_user"),
         InlineKeyboardButton(text="✉️ Сообщения пользователя по ID", callback_data="admin_view_msgs")],
        [InlineKeyboardButton(text="❓ Кто написал сообщение по ID", callback_data="admin_sender")],
        [InlineKeyboardButton(text="◀ Назад", callback_data="admin_panel")],
    ])


def admin_admins_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📋 Список админов", callback_data="admin_admins_list")],
        [InlineKeyboardButton(text="➕ Добавить админа", callback_data="admin_add_admin"),
         InlineKeyboardButton(text="➖ Удалить админа", callback_data="admin_remove_admin")],
        [InlineKeyboardButton(text="◀ Назад", callback_data="admin_panel")],
    ])


def noop_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="...", callback_data="noop")],
    ])


def msgs_page_kb(messages: list, page: int, total: int) -> InlineKeyboardMarkup:
    kb = []
    num_row = []
    for i, msg in enumerate(messages):
        num_row.append(InlineKeyboardButton(text=str(i + 1), callback_data=f"msg_info:{msg.id}"))
    kb.append(num_row)

    nav_row = []
    max_page = (total - 1) // 5
    if page > 0:
        nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"admin_msgs:{page - 1}"))
    nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{max_page + 1}", callback_data="noop"))
    if page < max_page:
        nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"admin_msgs:{page + 1}"))
    if nav_row:
        kb.append(nav_row)

    kb.append([InlineKeyboardButton(text="◀ Назад", callback_data="admin_panel")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def msg_info_kb(msg_id: int, sender_tg_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✉️ Все сообщения от этого отправителя",
            callback_data=f"sender_msgs:{sender_tg_id}:0:msg_info:{msg_id}",
        )],
        [InlineKeyboardButton(
            text="👤 Профиль отправителя",
            callback_data=f"view_user:{sender_tg_id}",
        )],
        [InlineKeyboardButton(text="◀ К списку сообщений", callback_data="admin_msgs:0")],
    ])


def sender_msgs_page_kb(sender_tg_id: int, messages: list, page: int, total: int, back_cb: str | None = None) -> InlineKeyboardMarkup:
    kb = []
    if len(messages) > 0:
        max_page = (total - 1) // 5
        if max_page > 0:
            nav_row = []
            if page > 0:
                nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"sender_msgs:{sender_tg_id}:{page - 1}" + (f":{back_cb}" if back_cb else "")))
            nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{max_page + 1}", callback_data="noop"))
            if page < max_page:
                nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"sender_msgs:{sender_tg_id}:{page + 1}" + (f":{back_cb}" if back_cb else "")))
            kb.append(nav_row)
    kb.append([InlineKeyboardButton(text="◀ Назад", callback_data=back_cb or f"view_user:{sender_tg_id}")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def lang_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Русский 🇷🇺", callback_data="lang:ru"),
         InlineKeyboardButton(text="English 🇬🇧", callback_data="lang:en")],
    ])


def reset_link_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="🔄 Сбросить ссылку", callback_data="reset_link")],
        [InlineKeyboardButton(text="Отмена", callback_data="cancel_reset")],
    ])


def admin_tools_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⛔ Бан / Разбан", callback_data="admin_ban_menu"),
         InlineKeyboardButton(text="📋 Список банов", callback_data="admin_banlist")],
        [InlineKeyboardButton(text="📢 Рассылка", callback_data="admin_broadcast"),
         InlineKeyboardButton(text="🧹 Очистка", callback_data="admin_cleanup")],
         [InlineKeyboardButton(text="📤 Экспорт CSV", callback_data="admin_export_csv"),
          InlineKeyboardButton(text="🔄 Сброс ссылки", callback_data="admin_reset_link_tool")],
        [InlineKeyboardButton(text="◀ Назад", callback_data="admin_panel")],
    ])


def stop_session_kb(lang: str = "ru") -> InlineKeyboardMarkup:
    from bot.locales import t
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=t("stop_btn", lang), callback_data="stop_session")],
    ])
