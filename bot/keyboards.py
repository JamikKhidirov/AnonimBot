from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def admin_menu_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика", callback_data="admin_stats"),
         InlineKeyboardButton(text="👥 Пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="✉️ Сообщения", callback_data="admin_msgs:0"),
         InlineKeyboardButton(text="👑 Админы", callback_data="admin_admins")],
        [InlineKeyboardButton(text="🔍 Поиск", callback_data="admin_search"),
         InlineKeyboardButton(text="📢 Реклама", callback_data="admin_ads")],
        [InlineKeyboardButton(text="🛠 Инструменты", callback_data="admin_tools")],
        [InlineKeyboardButton(text="⚙️ Для разработчика", callback_data="admin_dev")],
    ])


def back_kb(cb_data: str = "admin_panel") -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="◀ Назад", callback_data=cb_data)],
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
        num_row.append(InlineKeyboardButton(
            text=str(i + 1),
            callback_data=f"msg_info:{msg.id}:admin_msgs:{page}",
        ))
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


def msg_info_kb(msg_id: int, sender_tg_id: int, back_cb: str | None = None) -> InlineKeyboardMarkup:
    back_from_info = f"msg_info:{msg_id}" + (f":{back_cb}" if back_cb else "")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text="✉️ Все сообщения от этого отправителя",
            callback_data=f"sender_msgs:{sender_tg_id}:0:{back_from_info}",
        )],
        [InlineKeyboardButton(
            text="👤 Профиль отправителя",
            callback_data=f"view_user:{sender_tg_id}:{back_from_info}",
        )],
        [InlineKeyboardButton(text="◀ Назад", callback_data=back_cb or "admin_msgs:0")],
    ])


def sender_msgs_page_kb(sender_tg_id: int, messages: list, page: int, total: int, back_cb: str | None = None) -> InlineKeyboardMarkup:
    kb = []
    if len(messages) > 0:
        max_page = (total - 1) // 5
        if max_page > 0:
            nav_row = []
            prefix = f"sender_msgs:{sender_tg_id}:"
            if page > 0:
                nav_row.append(InlineKeyboardButton(
                    text="◀",
                    callback_data=f"{prefix}{page - 1}" + (f":{back_cb}" if back_cb else ""),
                ))
            nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{max_page + 1}", callback_data="noop"))
            if page < max_page:
                nav_row.append(InlineKeyboardButton(
                    text="▶",
                    callback_data=f"{prefix}{page + 1}" + (f":{back_cb}" if back_cb else ""),
                ))
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


# ─────────────── Реклама (adverts) ───────────────

def admin_ads_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="➕ Создать рекламу", callback_data="ad_create")],
        [InlineKeyboardButton(text="📋 Мои рекламы", callback_data="ad_list:0")],
        [InlineKeyboardButton(text="⚙️ Настройки рассылки", callback_data="ad_settings")],
        [InlineKeyboardButton(text="◀ Назад", callback_data="admin_panel")],
    ])


def ad_list_kb(ads: list, page: int, total: int, per_page: int = 5) -> InlineKeyboardMarkup:
    kb = []
    for ad in ads:
        name = ad.name or f"Реклама #{ad.id}"
        kb.append([InlineKeyboardButton(
            text=f"{'🟢' if ad.is_active else '⚪️'} {name}",
            callback_data=f"ad_view:{ad.id}:ad_list:{page}",
        )])

    nav_row = []
    max_page = (total - 1) // per_page
    if max_page > 0:
        if page > 0:
            nav_row.append(InlineKeyboardButton(text="◀", callback_data=f"ad_list:{page - 1}"))
        nav_row.append(InlineKeyboardButton(text=f"{page + 1}/{max_page + 1}", callback_data="noop"))
        if page < max_page:
            nav_row.append(InlineKeyboardButton(text="▶", callback_data=f"ad_list:{page + 1}"))
        kb.append(nav_row)

    kb.append([InlineKeyboardButton(text="➕ Создать", callback_data="ad_create")])
    kb.append([InlineKeyboardButton(text="◀ Назад", callback_data="admin_ads")])
    return InlineKeyboardMarkup(inline_keyboard=kb)


def ad_view_kb(ad_id: int, back_cb: str | None = None) -> InlineKeyboardMarkup:
    back_from_view = f"ad_view:{ad_id}" + (f":{back_cb}" if back_cb else "")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="✏️ Редактировать", callback_data=f"ad_edit_menu:{ad_id}:{back_from_view}")],
        [InlineKeyboardButton(text="🔄 Вкл / Выкл", callback_data=f"ad_toggle:{ad_id}:{back_from_view}")],
        [InlineKeyboardButton(text="📤 Отправить сейчас", callback_data=f"ad_send_now:{ad_id}")],
        [InlineKeyboardButton(text="👁 Предпросмотр", callback_data=f"ad_preview:{ad_id}:{back_from_view}")],
        [InlineKeyboardButton(text="🗑 Удалить", callback_data=f"ad_delete:{ad_id}:{back_from_view}")],
        [InlineKeyboardButton(text="◀ Назад", callback_data=back_cb or "ad_list:0")],
    ])


def ad_edit_menu_kb(ad_id: int, back_cb: str | None = None) -> InlineKeyboardMarkup:
    back_from_edit = f"ad_edit_menu:{ad_id}" + (f":{back_cb}" if back_cb else "")
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📝 Название", callback_data=f"ad_edit_field:{ad_id}:name:{back_from_edit}")],
        [InlineKeyboardButton(text="✍️ Текст (описание)", callback_data=f"ad_edit_field:{ad_id}:text:{back_from_edit}")],
        [InlineKeyboardButton(text="🖼 Медиа (фото/видео)", callback_data=f"ad_edit_field:{ad_id}:media:{back_from_edit}")],
        [InlineKeyboardButton(text="🔗 Кнопка", callback_data=f"ad_edit_field:{ad_id}:button:{back_from_edit}")],
        [InlineKeyboardButton(text="◀ Назад", callback_data=back_cb or f"ad_view:{ad_id}")],
    ])


def ad_settings_kb(config, back_cb: str = "admin_ads") -> InlineKeyboardMarkup:
    status = "🟢 ВКЛЮЧЕНА" if config.is_enabled else "🔴 ВЫКЛЮЧЕНА"
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"⏱ Интервал: {config.interval_seconds // 60} мин",
                              callback_data="ad_set_interval")],
        [InlineKeyboardButton(text=f"{'⏸ Выключить' if config.is_enabled else '▶ Включить'} рассылку",
                              callback_data="ad_toggle_scheduler")],
        [InlineKeyboardButton(text="📤 Отправить рекламу сейчас", callback_data="ad_send_now_active")],
        [InlineKeyboardButton(text="◀ Назад", callback_data=back_cb)],
    ])
