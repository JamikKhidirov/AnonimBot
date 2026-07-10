_t = {
    "ru": {
        # General
        "access_denied": "Доступ запрещён.",
        "dev_only": "Только для разработчика.",
        "back": "◀ Назад в админку",
        "no_data": "Нет данных.",
        "not_found": "Не найдено.",

        # /start
        "start_text": (
            "Привет! 👋\n\n"
            "Этот бот позволяет получать анонимные сообщения.\n\n"
            "📌 <b>Твоя ссылка для анонимных сообщений:</b>\n{link}\n\n"
            "📋 <b>Команды:</b>\n"
            "/start — получить свою ссылку\n"
            "/messages — посмотреть свои сообщения\n"
            "/stop — отписаться (выйти из текущего чата)\n"
            "/help — справка\n\n"
            "🔗 <i>Твоя ссылка активна, пока ты её не сбросишь.</i>"
        ),
        "start_shared": (
            "Привет! 👋\n\n"
            "Этот бот позволяет получать анонимные сообщения.\n\n"
            "📌 <b>Твоя ссылка для анонимных сообщений:</b>\n{link}\n\n"
            "Кому-то уже передана твоя ссылка, но у тебя уже есть активная."
        ),
        "chat_started": (
            "🔗 <b>Чат начат!</b>\n\n"
            "Теперь ты можешь писать анонимные сообщения владельцу этой ссылки.\n"
            "Он не узнает, кто ты.\n\n"
            "Просто напиши что-нибудь и отправь.\n"
            "/stop — выйти из чата."
        ),
        "session_expired": "Эта ссылка больше не активна.",
        "whois_btn": "👤 Кто это?",

        # /stop
        "stopped": "✅ Ты вышел из чата. Чтобы начать заново, нажми на чью-то ссылку.",

        # /messages
        "no_messages": "У тебя пока нет сообщений.",
        "your_messages": "📩 <b>Твои сообщения ({count}):</b>\n",

        # /help
        "help_text": (
            "ℹ️ <b>Справка</b>\n\n"
            "Это бот для анонимного общения.\n\n"
            "• Нажми на ссылку другого человека, чтобы написать ему анонимно\n"
            "• Получи свою ссылку через /start\n"
            "• Ответь на сообщение от бота — твой ответ уйдёт собеседнику\n"
            "• /stop — выйти из чата\n"
            "• /language — сменить язык\n\n"
            "Владельцы ссылок видят сообщения, но не знают, кто их отправил."
        ),

        # Anonymous message
        "no_session": (
            "Используй /start чтобы получить свою ссылку, "
            "или перейди по чьей-то ссылке чтобы написать анонимно."
        ),
        "msg_sent": "Сообщение отправлено анонимно!",
        "new_anon": "📩 <b>Новое анонимное сообщение!</b>\n\n{text}\n\nОтветь на это сообщение — твой ответ уйдёт анонимному отправителю.",
        "you_banned": "⛔ Ты забанен. Ты не можешь отправлять анонимные сообщения.",

        # Reply
        "reply_owner_header": "💬 <b>Ответ от владельца ссылки:</b>",
        "reply_sender_header": "💬 <b>Ответ от анонимного отправителя:</b>",
        "reply_sent_owner": "✅ Ответ отправлен анонимному отправителю!",
        "reply_sent_sender": "✅ Ответ отправлен владельцу ссылки!",
        "original_not_found": "Оригинальное сообщение не найдено.",
        "link_not_found": "Ссылка не найдена.",

        # Admin panel
        "admin_panel": "👮 <b>Админ панель</b>",
        "stats": "<b>📊 Статистика</b>\n\n👥 Пользователей: {users}\n🔗 Ссылок: {links}\n✉️ Сообщений: {msgs}",
        "all_users": "<b>👥 Все пользователи ({count}):</b>",
        "admin_mgmt": "👑 <b>Управление администраторами</b>",
        "no_admins": "Нет записей об администраторах.",
        "admins_list": "<b>Администраторы ({count}):</b>\n",

        # Admin commands
        "add_admin_usage": "Использование: /add_admin [user_id]",
        "add_admin_done": "✅ Пользователь <code>{id}</code> теперь админ.",
        "add_admin_notified": "🎉 Тебя назначили админом бота!",
        "remove_admin_usage": "Использование: /remove_admin [user_id]",
        "remove_admin_cant": "Нельзя убрать разработчика из админов.",
        "remove_admin_not_found": "Пользователь {id} не найден.",
        "remove_admin_done": "Пользователь <code>{id}</code> больше не админ.",
        "user_not_found": "Пользователь <code>{id}</code> не найден в БД.",

        "view_user_usage": "Использование: /view_user [user_id]",
        "view_messages_usage": "Использование: /view_messages [user_id]",
        "no_links": "У пользователя <code>{id}</code> нет ссылок.",
        "no_msgs_for_user": "Нет сообщений для пользователя <code>{id}</code>.",

        "sender_usage": "Использование: /sender [message_id]",
        "msg_not_found": "Сообщение #{id} не найдено.",

        "search_user_usage": "Использование: /search_user [id, username или имя]",
        "search_results_users": "<b>Результаты поиска «{query}» ({count}):</b>\n",
        "no_users_found": "Пользователи не найдены.",
        "search_msgs_usage": "Использование: /search_messages [текст]",
        "search_results_msgs": "<b>Результаты поиска «{query}» ({count}):</b>\n",
        "no_msgs_found": "Сообщения не найдены.",
        "search_subtitle": "🔍 <b>Поиск</b>\n\nВыбери тип поиска:",
        "search_user_title": "🔍 <b>Поиск пользователя</b>\n\nОтправь команду:\n<code>/search_user [id, username или имя]</code>",
        "search_msgs_title": "🔍 <b>Поиск сообщений</b>\n\nОтправь команду:\n<code>/search_messages [текст]</code>",
        "view_user_title": "👤 <b>Информация о пользователе</b>\n\nОтправь команду:\n<code>/view_user [user_id]</code>",
        "view_msgs_title": "📩 <b>Сообщения пользователя</b>\n\nОтправь команду:\n<code>/view_messages [user_id]</code>",
        "sender_title": "❓ <b>Кто написал сообщение</b>\n\nОтправь команду:\n<code>/sender [message_id]</code>",

        "dev_panel": (
            "<b>⚙️ Панель разработчика</b>\n\n"
            "<code>/add_admin [id]</code> — назначить админа\n"
            "<code>/remove_admin [id]</code> — убрать админа\n"
            "<code>/view_user [id]</code> — инфо о пользователе\n"
            "<code>/view_messages [id]</code> — сообщения пользователя\n"
            "<code>/sender [id]</code> — кто написал сообщение\n"
            "<code>/search_user [query]</code> — поиск пользователей\n"
            "<code>/search_messages [query]</code> — поиск сообщений\n"
            "<code>/ban [id]</code> — заблокировать пользователя\n"
            "<code>/unban [id]</code> — разблокировать\n"
            "<code>/broadcast [text]</code> — разослать всем\n"
            "<code>/export_csv</code> — выгрузить сообщения\n"
            "<code>/cleanup [days]</code> — удалить старые сообщения"
        ),

        # Messages list in admin
        "all_msgs_title": "<b>📩 Все сообщения (стр. {page}):</b>\n",
        "no_msgs_yet": "Сообщений пока нет.",
        "msgs_from_sender": "<b>✉️ Сообщения от пользователя {id} (стр. {page}):</b>\n",
        "no_msgs_from_sender": "У отправителя <code>{id}</code> нет сообщений.",

        # Message info
        "msg_info_title": "<b>📄 Сообщение #{id}</b>",
        "msg_sender": "<b>Отправитель:</b>",
        "msg_link_owner": "<b>Владелец ссылки:</b>",
        "msg_text": "<b>Текст:</b>",
        "msg_time": "<b>Время:</b>",
        "msg_total": "Всего отправлено: {count}",

        # User info
        "user_info_title": "<b>👤 Информация о пользователе</b>",
        "role_label": "Роль: {role}",
        "reg_date": "Зарегистрирован: {date}",
        "username_label": "Username: @{name}",
        "name_label": "Имя: {name}",

        # Whois
        "whois_title": "<b>👤 Отправитель анонимки</b>",
        "whois_time": "Время отправки: {time}",
        "whois_total": "Всего отправлено сообщений: {count}",
        "whois_text": "Текст: {text}",
        "whois_recent": "\n\n━━ <b>Последние сообщения:</b>",

        # /show
        "show_usage": "Ответь на анонимное сообщение от бота командой /show, чтобы увидеть кто его написал.",
        "not_anon_msg": "Это сообщение не является анонимным.",
        "show_title": "<b>👤 Отправитель анонимки</b>",
        "show_total": "Всего отправлено: {count}",

        # Language
        "lang_choose": "🌐 <b>Выбери язык / Choose language:</b>",
        "lang_changed": "✅ Язык изменён на русский.",
        "lang_changed_en": "✅ Language changed to English.",
        "lang_btn_ru": "Русский 🇷🇺",
        "lang_btn_en": "English 🇬🇧",

        # Ban
        "ban_usage": "Использование: /ban [user_id] [причина]",
        "ban_done": "✅ Пользователь <code>{id}</code> забанен.\nПричина: {reason}",
        "ban_already": "Пользователь <code>{id}</code> уже забанен.",
        "unban_usage": "Использование: /unban [user_id]",
        "unban_done": "✅ Пользователь <code>{id}</code> разбанен.",
        "unban_not_found": "Пользователь <code>{id}</code> не в бане.",
        "ban_list_title": "<b>⛔ Забаненные пользователи ({count}):</b>\n",
        "no_banned": "Нет забаненных пользователей.",
        "ban_reason": "Причина: {reason}",
        "ban_date": "Забанен: {date}",
        "ban_by": "Кем: {by}",

        # Broadcast
        "broadcast_usage": "Использование: /broadcast [текст]",
        "broadcast_start": "📤 Начинаю рассылку {count} пользователям...",
        "broadcast_done": "✅ Рассылка завершена. Отправлено: {sent}, ошибок: {errors}.",
        "broadcast_preview": "📢 <b>Рассылка от администрации</b>\n\n{text}",

        # Cleanup
        "cleanup_usage": "Использование: /cleanup [days]",
        "cleanup_done": "✅ Удалено старых сообщений: {count}.",

        # Export CSV
        "export_start": "📤 Генерирую CSV...",
        "export_error": "Ошибка при создании CSV.",

        # Link management
        "reset_link_confirm": (
            "🔗 <b>Сброс ссылки</b>\n\n"
            "Текущая ссылка будет деактивирована, создана новая.\n"
            "Все старые сообщения останутся, но новые по старой ссылке не пройдут.\n\n"
            "Точно сбросить?"
        ),
        "reset_link_done": "✅ Ссылка сброшена!\n\nТвоя новая ссылка:\n{link}",
        "reset_link_btn": "🔄 Сбросить ссылку",
        "cancel_btn": "Отмена",
        "link_reset_cancelled": "Сброс отменён.",
    },

    "en": {
        # General
        "access_denied": "Access denied.",
        "dev_only": "Developer only.",
        "back": "◀ Back to admin",
        "no_data": "No data.",
        "not_found": "Not found.",

        # /start
        "start_text": (
            "Hello! 👋\n\n"
            "This bot lets you receive anonymous messages.\n\n"
            "📌 <b>Your link for anonymous messages:</b>\n{link}\n\n"
            "📋 <b>Commands:</b>\n"
            "/start — get your link\n"
            "/messages — view your messages\n"
            "/stop — leave current chat\n"
            "/help — help\n\n"
            "🔗 <i>Your link is active until you reset it.</i>"
        ),
        "start_shared": (
            "Hello! 👋\n\n"
            "This bot lets you receive anonymous messages.\n\n"
            "📌 <b>Your link for anonymous messages:</b>\n{link}\n\n"
            "Someone already shared their link with you, but you already have an active link."
        ),
        "chat_started": (
            "🔗 <b>Chat started!</b>\n\n"
            "You can now send anonymous messages to the owner of this link.\n"
            "They won't know who you are.\n\n"
            "Just type something and send.\n"
            "/stop — leave the chat."
        ),
        "session_expired": "This link is no longer active.",
        "whois_btn": "👤 Who is this?",

        # /stop
        "stopped": "✅ You left the chat. Click someone's link to start again.",

        # /messages
        "no_messages": "You have no messages yet.",
        "your_messages": "📩 <b>Your messages ({count}):</b>\n",

        # /help
        "help_text": (
            "ℹ️ <b>Help</b>\n\n"
            "This bot is for anonymous communication.\n\n"
            "• Click someone's link to send them an anonymous message\n"
            "• Get your own link via /start\n"
            "• Reply to a bot message — your answer will go to the other person\n"
            "• /stop — leave the chat\n"
            "• /language — change language\n\n"
            "Link owners see messages but don't know who sent them."
        ),

        # Anonymous message
        "no_session": (
            "Use /start to get your link, "
            "or click someone's link to send an anonymous message."
        ),
        "msg_sent": "Message sent anonymously!",
        "new_anon": "📩 <b>New anonymous message!</b>\n\n{text}\n\nReply to this message — your answer will go to the anonymous sender.",
        "you_banned": "⛔ You are banned. You cannot send anonymous messages.",

        # Reply
        "reply_owner_header": "💬 <b>Reply from link owner:</b>",
        "reply_sender_header": "💬 <b>Reply from anonymous sender:</b>",
        "reply_sent_owner": "✅ Reply sent to anonymous sender!",
        "reply_sent_sender": "✅ Reply sent to link owner!",
        "original_not_found": "Original message not found.",
        "link_not_found": "Link not found.",

        # Admin panel
        "admin_panel": "👮 <b>Admin Panel</b>",
        "stats": "<b>📊 Statistics</b>\n\n👥 Users: {users}\n🔗 Links: {links}\n✉️ Messages: {msgs}",
        "all_users": "<b>👥 All users ({count}):</b>",
        "admin_mgmt": "👑 <b>Admin Management</b>",
        "no_admins": "No admin records.",
        "admins_list": "<b>Admins ({count}):</b>\n",

        # Admin commands
        "add_admin_usage": "Usage: /add_admin [user_id]",
        "add_admin_done": "✅ User <code>{id}</code> is now an admin.",
        "add_admin_notified": "🎉 You've been made a bot admin!",
        "remove_admin_usage": "Usage: /remove_admin [user_id]",
        "remove_admin_cant": "Cannot remove developer from admins.",
        "remove_admin_not_found": "User {id} not found.",
        "remove_admin_done": "User <code>{id}</code> is no longer an admin.",
        "user_not_found": "User <code>{id}</code> not found in DB.",

        "view_user_usage": "Usage: /view_user [user_id]",
        "view_messages_usage": "Usage: /view_messages [user_id]",
        "no_links": "User <code>{id}</code> has no links.",
        "no_msgs_for_user": "No messages for user <code>{id}</code>.",

        "sender_usage": "Usage: /sender [message_id]",
        "msg_not_found": "Message #{id} not found.",

        "search_user_usage": "Usage: /search_user [id, username or name]",
        "search_results_users": "<b>Search results for «{query}» ({count}):</b>\n",
        "no_users_found": "No users found.",
        "search_msgs_usage": "Usage: /search_messages [text]",
        "search_results_msgs": "<b>Search results for «{query}» ({count}):</b>\n",
        "no_msgs_found": "No messages found.",
        "search_subtitle": "🔍 <b>Search</b>\n\nChoose search type:",
        "search_user_title": "🔍 <b>Search User</b>\n\nSend command:\n<code>/search_user [id, username or name]</code>",
        "search_msgs_title": "🔍 <b>Search Messages</b>\n\nSend command:\n<code>/search_messages [text]</code>",
        "view_user_title": "👤 <b>User Info</b>\n\nSend command:\n<code>/view_user [user_id]</code>",
        "view_msgs_title": "📩 <b>User Messages</b>\n\nSend command:\n<code>/view_messages [user_id]</code>",
        "sender_title": "❓ <b>Who sent the message</b>\n\nSend command:\n<code>/sender [message_id]</code>",

        "dev_panel": (
            "<b>⚙️ Developer Panel</b>\n\n"
            "<code>/add_admin [id]</code> — add admin\n"
            "<code>/remove_admin [id]</code> — remove admin\n"
            "<code>/view_user [id]</code> — user info\n"
            "<code>/view_messages [id]</code> — user messages\n"
            "<code>/sender [id]</code> — who wrote the message\n"
            "<code>/search_user [query]</code> — search users\n"
            "<code>/search_messages [query]</code> — search messages\n"
            "<code>/ban [id]</code> — ban user\n"
            "<code>/unban [id]</code> — unban\n"
            "<code>/broadcast [text]</code> — broadcast to all\n"
            "<code>/export_csv</code> — export messages\n"
            "<code>/cleanup [days]</code> — delete old messages"
        ),

        # Messages list in admin
        "all_msgs_title": "<b>📩 All messages (page {page}):</b>\n",
        "no_msgs_yet": "No messages yet.",
        "msgs_from_sender": "<b>✉️ Messages from user {id} (page {page}):</b>\n",
        "no_msgs_from_sender": "Sender <code>{id}</code> has no messages.",

        # Message info
        "msg_info_title": "<b>📄 Message #{id}</b>",
        "msg_sender": "<b>Sender:</b>",
        "msg_link_owner": "<b>Link owner:</b>",
        "msg_text": "<b>Text:</b>",
        "msg_time": "<b>Time:</b>",
        "msg_total": "Total sent: {count}",

        # User info
        "user_info_title": "<b>👤 User Info</b>",
        "role_label": "Role: {role}",
        "reg_date": "Registered: {date}",
        "username_label": "Username: @{name}",
        "name_label": "Name: {name}",

        # Whois
        "whois_title": "<b>👤 Anonymous Sender</b>",
        "whois_time": "Sent at: {time}",
        "whois_total": "Total messages: {count}",
        "whois_text": "Text: {text}",
        "whois_recent": "\n\n━━ <b>Recent messages:</b>",

        # /show
        "show_usage": "Reply to an anonymous bot message with /show to see who sent it.",
        "not_anon_msg": "This message is not anonymous.",
        "show_title": "<b>👤 Anonymous Sender</b>",
        "show_total": "Total sent: {count}",

        # Language
        "lang_choose": "🌐 <b>Choose language:</b>",
        "lang_changed": "✅ Language changed to Russian.",
        "lang_changed_en": "✅ Language changed to English.",
        "lang_btn_ru": "Russian 🇷🇺",
        "lang_btn_en": "English 🇬🇧",

        # Ban
        "ban_usage": "Usage: /ban [user_id] [reason]",
        "ban_done": "✅ User <code>{id}</code> banned.\nReason: {reason}",
        "ban_already": "User <code>{id}</code> is already banned.",
        "unban_usage": "Usage: /unban [user_id]",
        "unban_done": "✅ User <code>{id}</code> unbanned.",
        "unban_not_found": "User <code>{id}</code> is not banned.",
        "ban_list_title": "<b>⛔ Banned users ({count}):</b>\n",
        "no_banned": "No banned users.",
        "ban_reason": "Reason: {reason}",
        "ban_date": "Banned: {date}",
        "ban_by": "By: {by}",

        # Broadcast
        "broadcast_usage": "Usage: /broadcast [text]",
        "broadcast_start": "📤 Broadcasting to {count} users...",
        "broadcast_done": "✅ Broadcast finished. Sent: {sent}, errors: {errors}.",
        "broadcast_preview": "📢 <b>Broadcast from admins</b>\n\n{text}",

        # Cleanup
        "cleanup_usage": "Usage: /cleanup [days]",
        "cleanup_done": "✅ Old messages deleted: {count}.",

        # Export CSV
        "export_start": "📤 Generating CSV...",
        "export_error": "Error generating CSV.",

        # Link management
        "reset_link_confirm": (
            "🔗 <b>Reset link</b>\n\n"
            "Your current link will be deactivated and a new one created.\n"
            "Old messages will remain, but new ones won't work with the old link.\n\n"
            "Are you sure?"
        ),
        "reset_link_done": "✅ Link reset!\n\nYour new link:\n{link}",
        "reset_link_btn": "🔄 Reset link",
        "cancel_btn": "Cancel",
        "link_reset_cancelled": "Reset cancelled.",
    },
}


def t(key: str, lang: str = "ru") -> str:
    return _t.get(lang, _t["ru"]).get(key, _t["ru"].get(key, key))


_roles = {
    ("ru", True, True): "🛡 Разработчик",
    ("ru", False, True): "👑 Админ",
    ("ru", False, False): "👤 Пользователь",
    ("en", True, True): "🛡 Developer",
    ("en", False, True): "👑 Admin",
    ("en", False, False): "👤 User",
}


def role_label(lang: str, is_dev: bool, is_admin: bool) -> str:
    return _roles.get((lang, is_dev, is_admin),
                      _roles.get(("ru", is_dev, is_admin), "Unknown"))
