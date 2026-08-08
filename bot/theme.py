"""Visual theme for the bot.

Telegram does not support arbitrary text colors inside messages, so the theme
is the bot's "signature": an accent emoji + bolded headers (a color stripe is
rendered via the mention-style link, picking up the reader's app accent).

The developer can change THEME_ACCENT / THEME_COLOR in .env (defaults) or
live from the /admin panel — changes are stored in the DB via bot_settings
and applied instantly.
"""

import os

from bot.database import get_setting, set_setting

_ACCENT_EMOJI = (os.getenv("THEME_ACCENT") or "🔶").strip()
# Kept for reference/reporting; Telegram ignores raw hex colors.
_ACCENT_COLOR = (os.getenv("THEME_COLOR") or "#F59E0B").strip().upper()

_DUMMY_LINK_ID = 5000000000


def _emoji() -> str:
    return _ACCENT_EMOJI


def _color() -> str:
    return _ACCENT_COLOR


def current() -> tuple[str, str]:
    return _emoji(), _color()


async def load_theme():
    """Loads theme overrides from the DB (called once at startup)."""
    global _ACCENT_EMOJI, _ACCENT_COLOR
    e = await get_setting("theme.emoji")
    if e:
        _ACCENT_EMOJI = e
    c = await get_setting("theme.color")
    if c:
        _ACCENT_COLOR = c.upper()


async def set_theme(emoji: str | None = None, color: str | None = None):
    global _ACCENT_EMOJI, _ACCENT_COLOR
    if emoji:
        _ACCENT_EMOJI = emoji
        await set_setting("theme.emoji", emoji)
    if color:
        _ACCENT_COLOR = color.upper()
        await set_setting("theme.color", color.upper())


async def reset_theme():
    global _ACCENT_EMOJI, _ACCENT_COLOR
    _ACCENT_EMOJI = (os.getenv("THEME_ACCENT") or "🔶").strip()
    _ACCENT_COLOR = (os.getenv("THEME_COLOR") or "#F59E0B").strip().upper()
    await set_setting("theme.emoji", _ACCENT_EMOJI)
    await set_setting("theme.color", _ACCENT_COLOR)


def accent(text: str) -> str:
    """Renders text in the app accent color via a mention-style link."""
    return f"<a href=\"tg://user?id={_DUMMY_LINK_ID}\">{text}</a>"


def head(title: str) -> str:
    """Themed header line used at the top of bot messages."""
    return f"{_emoji()} <b>{title}</b>"


def card(title: str, body: str) -> str:
    """Title + body wrapped in a blockquote card."""
    return f"<blockquote>{head(title)}\n\n{body}</blockquote>"


def stars(n: int = 0) -> str:
    n = max(0, min(5, int(n)))
    return "⭐" * n + "☆" * (5 - n)