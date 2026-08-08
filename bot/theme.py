"""Visual theme for the bot.

Telegram does not support arbitrary text colors inside messages, so the theme
is used as the bot's "signature": an accent emoji + bolded headers + a color
stripe rendered via the mention-style link (it picks up the reader's app
accent color). The developer can change THEME_ACCENT / THEME_COLOR in .env.
"""

import os

ACCENT_EMOJI = (os.getenv("THEME_ACCENT") or "🔶").strip()
# Kept for reference/reporting; Telegram ignores raw hex colors, but some
# front-ends (e.g. export/HTML reports) can use the accent value.
ACCENT_COLOR = (os.getenv("THEME_COLOR") or "#F59E0B").strip().upper()

_DUMMY_LINK_ID = 5000000000


def accent(text: str) -> str:
    """Renders text in the app accent color via a mention-style link."""
    return f"<a href=\"tg://user?id={_DUMMY_LINK_ID}\">{text}</a>"


def head(title: str) -> str:
    """Themed header line used at the top of bot messages."""
    return f"{ACCENT_EMOJI} <b>{title}</b>"


def card(title: str, body: str) -> str:
    """Title + body wrapped in a blockquote card."""
    return f"<blockquote>{head(title)}\n\n{body}</blockquote>"


def stars(n: int = 0) -> str:
    n = max(0, min(5, int(n)))
    return "⭐" * n + "☆" * (5 - n)