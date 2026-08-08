import secrets
import csv
import io
from datetime import datetime, timedelta

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean,
    DateTime, ForeignKey, select, delete, func, or_, text, UniqueConstraint,
)
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, relationship, selectinload

from bot.config import DATABASE_URL, DEVELOPER_ID


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    username = Column(String(255), nullable=True)
    full_name = Column(String(255), nullable=True)
    is_admin = Column(Boolean, default=False)
    is_developer = Column(Boolean, default=False)
    language = Column(String(5), default="ru")
    referral_code = Column(String(64), unique=True, nullable=True)
    referral_bonus_until = Column(DateTime, nullable=True)
    premium_plus = Column(Boolean, default=False)
    ladder_rewarded = Column(Integer, default=0)
    custom_greeting = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    links = relationship("ChatLink", back_populates="user")


class ChatLink(Base):
    __tablename__ = "chat_links"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String(64), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
    view_count = Column(Integer, default=0)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="links")
    messages = relationship("Message", back_populates="link", lazy="dynamic")


class Message(Base):
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True)
    link_id = Column(Integer, ForeignKey("chat_links.id"), nullable=False)
    sender_id = Column(BigInteger, nullable=False)
    sender_username = Column(String(255), nullable=True)
    sender_full_name = Column(String(255), nullable=True)
    text = Column(Text, nullable=True)
    content_type = Column(String(32), default="text")
    file_id = Column(String(512), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    link = relationship("ChatLink", back_populates="messages")


class ActiveSession(Base):
    __tablename__ = "active_sessions"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    link_code = Column(String(64), ForeignKey("chat_links.code"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class Admin(Base):
    __tablename__ = "admins"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    added_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class ForwardedMessage(Base):
    __tablename__ = "forwarded_messages"

    id = Column(Integer, primary_key=True)
    bot_message_id = Column(Integer, nullable=False)
    owner_tg_id = Column(BigInteger, nullable=False)
    original_msg_id = Column(Integer, ForeignKey("messages.id"), nullable=False)
    reply_text = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class BannedUser(Base):
    __tablename__ = "banned_users"

    id = Column(Integer, primary_key=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False)
    reason = Column(String(500), nullable=True)
    banned_by = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)


class MutedSender(Base):
    """Owner muted a specific anonymous sender (mute by sender, not ban everyone)."""
    __tablename__ = "muted_senders"

    id = Column(Integer, primary_key=True)
    owner_tg_id = Column(BigInteger, nullable=False)
    sender_id = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    __table_args__ = (UniqueConstraint("owner_tg_id", "sender_id", name="uq_muted"),)


class ChannelGate(Base):
    """Optional required-subscription channel. When set, anonymous users must subscribe first."""
    __tablename__ = "channel_gate"

    id = Column(Integer, primary_key=True)
    channel = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)


class Referral(Base):
    __tablename__ = "referrals"

    id = Column(Integer, primary_key=True)
    referrer_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    referee_id = Column(Integer, ForeignKey("users.id"), nullable=False, unique=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AdvertConfig(Base):
    __tablename__ = "advert_config"

    id = Column(Integer, primary_key=True)
    interval_seconds = Column(Integer, default=1800)
    last_sent_at = Column(DateTime, nullable=True)
    is_enabled = Column(Boolean, default=False)


class Advert(Base):
    __tablename__ = "adverts"

    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=True)
    text = Column(Text, nullable=True)
    photo_file_id = Column(String(512), nullable=True)
    video_file_id = Column(String(512), nullable=True)
    button_text = Column(String(100), nullable=True)
    button_url = Column(String(500), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class PremiumPlan(Base):
    __tablename__ = "premium_plans"

    id = Column(Integer, primary_key=True)
    name = Column(String(100), nullable=False)
    days = Column(Integer, nullable=False)
    price = Column(Integer, nullable=False)


class PremiumSubscription(Base):
    __tablename__ = "premium_subscriptions"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    start_date = Column(DateTime, default=datetime.utcnow)
    end_date = Column(DateTime, nullable=False)
    is_active = Column(Boolean, default=True)


class PendingDelivery(Base):
    __tablename__ = "pending_deliveries"

    id = Column(Integer, primary_key=True)
    message_id = Column(Integer, ForeignKey("messages.id"), unique=True, nullable=False)
    payload = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_log"

    id = Column(Integer, primary_key=True)
    admin_tg_id = Column(BigInteger, nullable=False)
    action = Column(String(100), nullable=False)
    target_desc = Column(String(500), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)


engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── Migration: add missing columns for existing DBs ──
    migrations = [
        ("users", "language", "VARCHAR(5) DEFAULT 'ru'"),
        ("forwarded_messages", "reply_text", "TEXT"),
        ("messages", "content_type", "VARCHAR(32) DEFAULT 'text'"),
        ("messages", "file_id", "VARCHAR(512)"),
        ("users", "referral_code", "VARCHAR(64)"),
        ("users", "referral_bonus_until", "DATETIME"),
        ("adverts", "name", "VARCHAR(200)"),
        ("adverts", "photo_file_id", "VARCHAR(512)"),
        ("adverts", "button_text", "VARCHAR(100)"),
        ("adverts", "button_url", "VARCHAR(500)"),
        ("advert_config", "is_enabled", "BOOLEAN DEFAULT 0"),
        ("users", "premium_plus", "BOOLEAN DEFAULT 0"),
        ("users", "custom_greeting", "TEXT"),
        ("users", "ladder_rewarded", "INTEGER DEFAULT 0"),
        ("chat_links", "view_count", "INTEGER DEFAULT 0"),
    ]
    for table, column, col_type in migrations:
        try:
            async with engine.connect() as conn:
                await conn.execute(
                    text(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
                )
                await conn.commit()
        except Exception:
            pass  # column already exists


async def get_or_create_user(
    telegram_id: int,
    username: str | None,
    full_name: str | None,
    language: str | None = None,
) -> User:
    from sqlalchemy.exc import IntegrityError
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.username = username
            user.full_name = full_name
            if telegram_id == DEVELOPER_ID:
                user.is_developer = True
                user.is_admin = True
            await session.commit()
            await session.refresh(user)
            return user
        user = User(telegram_id=telegram_id, username=username, full_name=full_name)
        if language:
            user.language = language
        if telegram_id == DEVELOPER_ID:
            user.is_developer = True
            user.is_admin = True
        session.add(user)
        try:
            await session.commit()
        except IntegrityError:
            await session.rollback()
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            if user:
                user.username = username
                user.full_name = full_name
                if telegram_id == DEVELOPER_ID:
                    user.is_developer = True
                    user.is_admin = True
                await session.commit()
                await session.refresh(user)
                return user
            raise
        await session.refresh(user)
        return user


async def get_user(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        return result.scalar_one_or_none()


async def get_user_with_links(telegram_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).options(selectinload(User.links)).where(User.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def get_user_by_db_id(user_id: int) -> User | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).options(selectinload(User.links)).where(User.id == user_id)
        )
        return result.scalar_one_or_none()


async def get_all_users() -> list[User]:
    async with async_session() as session:
        result = await session.execute(select(User).order_by(User.id))
        return list(result.scalars().all())


async def search_users(query: str) -> list[User]:
    async with async_session() as session:
        stmt = select(User)
        if query.isdigit():
            stmt = stmt.where(User.telegram_id == int(query))
        else:
            stmt = stmt.where(
                or_(
                    User.username.ilike(f"%{query}%"),
                    User.full_name.ilike(f"%{query}%"),
                )
            )
        result = await session.execute(stmt.order_by(User.id).limit(30))
        return list(result.scalars().all())


async def set_admin(telegram_id: int, is_admin: bool, added_by: int = 0):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.is_admin = is_admin
            await session.commit()
        if is_admin:
            exists = await session.execute(select(Admin).where(Admin.telegram_id == telegram_id))
            if not exists.scalar_one_or_none():
                session.add(Admin(telegram_id=telegram_id, added_by=added_by))
                await session.commit()
        else:
            await session.execute(delete(Admin).where(Admin.telegram_id == telegram_id))
            await session.commit()


async def get_all_admin_records() -> list[Admin]:
    async with async_session() as session:
        result = await session.execute(select(Admin).order_by(Admin.id))
        return list(result.scalars().all())


async def get_or_create_link(user_id: int) -> ChatLink:
    async with async_session() as session:
        result = await session.execute(
            select(ChatLink).options(selectinload(ChatLink.user)).where(
                ChatLink.user_id == user_id, ChatLink.is_active == True
            )
        )
        link = result.scalar_one_or_none()
        if link:
            return link
        code = secrets.token_urlsafe(16)
        link = ChatLink(user_id=user_id, code=code)
        session.add(link)
        await session.commit()
        result = await session.execute(
            select(ChatLink).options(selectinload(ChatLink.user)).where(ChatLink.id == link.id)
        )
        return result.scalar_one()


async def get_link_by_code(code: str) -> ChatLink | None:
    async with async_session() as session:
        result = await session.execute(
            select(ChatLink).options(selectinload(ChatLink.user)).where(
                ChatLink.code == code, ChatLink.is_active == True
            )
        )
        return result.scalar_one_or_none()


async def get_link_by_id(link_id: int) -> ChatLink | None:
    async with async_session() as session:
        result = await session.execute(
            select(ChatLink).options(selectinload(ChatLink.user)).where(ChatLink.id == link_id)
        )
        return result.scalar_one_or_none()


# ───── Link statistics ─────

async def bump_link_view(link_id: int):
    async with async_session() as session:
        result = await session.execute(select(ChatLink).where(ChatLink.id == link_id))
        link = result.scalar_one_or_none()
        if link:
            link.view_count = (link.view_count or 0) + 1
            await session.commit()


async def get_link_stats(link_id: int) -> dict:
    """Returns views, total messages and per-day counts (last 7 days)."""
    async with async_session() as session:
        result = await session.execute(select(ChatLink).where(ChatLink.id == link_id))
        link = result.scalar_one_or_none()
        views = (link.view_count or 0) if link else 0

        total = await session.execute(
            select(func.count(Message.id)).where(Message.link_id == link_id)
        )
        total_msgs = total.scalar() or 0

        daily_result = await session.execute(
            select(func.date(Message.created_at).label("day"), func.count(Message.id))
            .where(Message.link_id == link_id)
            .group_by("day")
            .order_by("day")
        )
        daily = [(str(day), count) for day, count in daily_result.all()][-7:]
    return {"views": views, "total": total_msgs, "daily": daily}


async def create_message(
    link_id: int, sender_id: int, text: str | None = None,
    content_type: str = "text", file_id: str | None = None,
    sender_username: str | None = None, sender_full_name: str | None = None,
) -> Message:
    async with async_session() as session:
        msg = Message(
            link_id=link_id,
            sender_id=sender_id,
            sender_username=sender_username,
            sender_full_name=sender_full_name,
            text=text,
            content_type=content_type,
            file_id=file_id,
        )
        session.add(msg)
        await session.commit()
        await session.refresh(msg)
        return msg


async def get_messages_for_link(link_id: int, limit: int = 50) -> list[Message]:
    async with async_session() as session:
        result = await session.execute(
            select(Message).where(Message.link_id == link_id)
            .order_by(Message.created_at.desc()).limit(limit)
        )
        return list(result.scalars().all())


async def get_all_messages(page: int = 0, per_page: int = 5) -> tuple[list[Message], int]:
    async with async_session() as session:
        count_result = await session.execute(select(func.count(Message.id)))
        total = count_result.scalar()
        result = await session.execute(
            select(Message).order_by(Message.created_at.desc())
            .offset(page * per_page).limit(per_page)
        )
        return list(result.scalars().all()), total


async def get_message_by_id(message_id: int) -> Message | None:
    async with async_session() as session:
        result = await session.execute(select(Message).where(Message.id == message_id))
        return result.scalar_one_or_none()


async def search_messages(query: str) -> list[Message]:
    async with async_session() as session:
        result = await session.execute(
            select(Message).where(Message.text.ilike(f"%{query}%"))
            .order_by(Message.created_at.desc()).limit(30)
        )
        return list(result.scalars().all())


async def get_messages_by_sender_id(
    sender_id: int, page: int = 0, per_page: int = 5
) -> tuple[list[Message], int]:
    async with async_session() as session:
        count_result = await session.execute(
            select(func.count(Message.id)).where(Message.sender_id == sender_id)
        )
        total = count_result.scalar()
        result = await session.execute(
            select(Message).where(Message.sender_id == sender_id)
            .order_by(Message.created_at.desc())
            .offset(page * per_page).limit(per_page)
        )
        return list(result.scalars().all()), total


async def get_sender_message_count(sender_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(
            select(func.count(Message.id)).where(Message.sender_id == sender_id)
        )
        return result.scalar()


async def set_active_session(telegram_id: int, link_code: str):
    async with async_session() as session:
        result = await session.execute(
            select(ActiveSession).where(ActiveSession.telegram_id == telegram_id)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.link_code = link_code
        else:
            session.add(ActiveSession(telegram_id=telegram_id, link_code=link_code))
        await session.commit()


async def get_active_session(telegram_id: int) -> ActiveSession | None:
    async with async_session() as session:
        result = await session.execute(
            select(ActiveSession).where(ActiveSession.telegram_id == telegram_id)
        )
        return result.scalar_one_or_none()


async def clear_active_session(telegram_id: int):
    async with async_session() as session:
        await session.execute(
            delete(ActiveSession).where(ActiveSession.telegram_id == telegram_id)
        )
        await session.commit()


async def save_forwarded_message(bot_message_id: int, owner_tg_id: int, original_msg_id: int, reply_text: str | None = None):
    async with async_session() as session:
        session.add(ForwardedMessage(
            bot_message_id=bot_message_id,
            owner_tg_id=owner_tg_id,
            original_msg_id=original_msg_id,
            reply_text=reply_text,
        ))
        await session.commit()


async def get_forwarded_message(bot_message_id: int, owner_tg_id: int) -> ForwardedMessage | None:
    async with async_session() as session:
        result = await session.execute(
            select(ForwardedMessage).where(
                ForwardedMessage.bot_message_id == bot_message_id,
                ForwardedMessage.owner_tg_id == owner_tg_id,
            )
        )
        return result.scalar_one_or_none()


async def get_last_forwarded_for_user(owner_tg_id: int, original_msg_id: int) -> ForwardedMessage | None:
    async with async_session() as session:
        result = await session.execute(
            select(ForwardedMessage)
            .where(
                ForwardedMessage.owner_tg_id == owner_tg_id,
                ForwardedMessage.original_msg_id == original_msg_id,
            )
            .order_by(ForwardedMessage.id.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()


async def get_forwarded_for_message(original_msg_id: int) -> list[ForwardedMessage]:
    async with async_session() as session:
        result = await session.execute(
            select(ForwardedMessage).where(ForwardedMessage.original_msg_id == original_msg_id)
        )
        return list(result.scalars().all())


async def delete_forwarded_for_message(original_msg_id: int):
    async with async_session() as session:
        await session.execute(
            delete(ForwardedMessage).where(ForwardedMessage.original_msg_id == original_msg_id)
        )
        await session.commit()


# ───── Undo send (pending deliveries) ─────

async def create_pending_delivery(message_id: int, payload: str | None = None):
    async with async_session() as session:
        session.add(PendingDelivery(message_id=message_id, payload=payload))
        await session.commit()


async def get_pending_delivery(message_id: int) -> PendingDelivery | None:
    async with async_session() as session:
        result = await session.execute(
            select(PendingDelivery).where(PendingDelivery.message_id == message_id)
        )
        return result.scalar_one_or_none()


async def delete_pending_delivery(message_id: int):
    async with async_session() as session:
        await session.execute(
            delete(PendingDelivery).where(PendingDelivery.message_id == message_id)
        )
        await session.commit()


async def delete_message_row(message_id: int):
    async with async_session() as session:
        await session.execute(delete(Message).where(Message.id == message_id))
        await session.commit()


async def get_message_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(Message.id)))
        return result.scalar()


async def get_user_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(User.id)))
        return result.scalar()


async def get_link_count() -> int:
    async with async_session() as session:
        result = await session.execute(select(func.count(ChatLink.id)))
        return result.scalar()


# ───── Language ─────

def detect_language(lang_code: str | None) -> str:
    """Maps Telegram language_code (e.g. 'en-US') to bot locale ('ru'/'en')."""
    if lang_code and lang_code.lower().startswith("en"):
        return "en"
    return "ru"


async def set_user_language(telegram_id: int, lang: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.language = lang
            await session.commit()


# ───── Mute by owner ─────

async def mute_sender(owner_tg_id: int, sender_id: int):
    async with async_session() as session:
        exists = await session.execute(
            select(MutedSender).where(
                MutedSender.owner_tg_id == owner_tg_id,
                MutedSender.sender_id == sender_id,
            )
        )
        if not exists.scalar_one_or_none():
            from sqlalchemy.exc import IntegrityError
            try:
                session.add(MutedSender(owner_tg_id=owner_tg_id, sender_id=sender_id))
                await session.commit()
            except IntegrityError:
                await session.rollback()


async def unmute_sender(owner_tg_id: int, sender_id: int):
    async with async_session() as session:
        await session.execute(
            delete(MutedSender).where(
                MutedSender.owner_tg_id == owner_tg_id,
                MutedSender.sender_id == sender_id,
            )
        )
        await session.commit()


async def is_muted(owner_tg_id: int, sender_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(MutedSender).where(
                MutedSender.owner_tg_id == owner_tg_id,
                MutedSender.sender_id == sender_id,
            )
        )
        return result.scalar_one_or_none() is not None


# ───── Channel gate (subscribe to use) ─────

async def get_channel_gate() -> ChannelGate | None:
    async with async_session() as session:
        result = await session.execute(
            select(ChannelGate).where(ChannelGate.is_active == True).limit(1)
        )
        return result.scalar_one_or_none()


async def set_channel_gate(channel: str | None):
    """Set or disable (None) the required channel for sending messages."""
    async with async_session() as session:
        await session.execute(
            delete(ChannelGate).where(ChannelGate.is_active == True)
        )
        if channel:
            session.add(ChannelGate(channel=channel, is_active=True))
        await session.commit()


# ───── Ban ─────

async def ban_user(telegram_id: int, banned_by: int, reason: str | None = None):
    async with async_session() as session:
        exists = await session.execute(select(BannedUser).where(BannedUser.telegram_id == telegram_id))
        if not exists.scalar_one_or_none():
            session.add(BannedUser(telegram_id=telegram_id, banned_by=banned_by, reason=reason))
            await session.commit()


async def unban_user(telegram_id: int):
    async with async_session() as session:
        await session.execute(delete(BannedUser).where(BannedUser.telegram_id == telegram_id))
        await session.commit()


async def is_banned(telegram_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(BannedUser).where(BannedUser.telegram_id == telegram_id))
        return result.scalar_one_or_none() is not None


async def get_all_banned() -> list[BannedUser]:
    async with async_session() as session:
        result = await session.execute(select(BannedUser).order_by(BannedUser.id))
        return list(result.scalars().all())


# ───── Audit log ─────

async def log_audit(admin_tg_id: int, action: str, target_desc: str | None = None):
    try:
        async with async_session() as session:
            session.add(AuditLog(admin_tg_id=admin_tg_id, action=action, target_desc=target_desc))
            await session.commit()
    except Exception:
        pass


async def get_audit_log(limit: int = 40) -> list[AuditLog]:
    async with async_session() as session:
        result = await session.execute(
            select(AuditLog).order_by(AuditLog.id.desc()).limit(limit)
        )
        return list(result.scalars().all())


# ───── Reset / deactivate link ─────

async def deactivate_link(telegram_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(
            select(User).options(selectinload(User.links)).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user or not user.links:
            return False
        for link in user.links:
            link.is_active = False
        await session.commit()
        return True


async def reset_link(telegram_id: int) -> ChatLink | None:
    async with async_session() as session:
        result = await session.execute(
            select(User).options(selectinload(User.links)).where(User.telegram_id == telegram_id)
        )
        user = result.scalar_one_or_none()
        if not user:
            return None
        for link in user.links:
            link.is_active = False
        new_code = secrets.token_urlsafe(16)
        new_link = ChatLink(user_id=user.id, code=new_code)
        session.add(new_link)
        await session.commit()
        await session.refresh(new_link)
        return new_link


# ───── Referral system ─────

async def get_or_create_referral_code(telegram_id: int) -> str:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return ""
        if user.referral_code:
            return user.referral_code
        user.referral_code = "ref_" + secrets.token_urlsafe(16)
        await session.commit()
        return user.referral_code


async def process_referral(referee_tg_id: int, referral_code: str) -> tuple[User | None, list[str]]:
    """Registers a referral, grants +10 hours of whois bonus and ladder milestones.

    Ladder:
      - 3 friends  -> extra week of 'whois' bonus
      - 10 friends -> 50% discount on Premium
      - 25 friends -> 1 month of Premium
    Returns (referrer or None, list of milestone labels won).
"""
    if not referral_code:
        return None, []
    async with async_session() as session:
        result = await session.execute(select(User).where(User.referral_code == referral_code))
        referrer = result.scalar_one_or_none()
        if not referrer:
            return None, []

        result = await session.execute(select(User).where(User.telegram_id == referee_tg_id))
        referee = result.scalar_one_or_none()
        if not referee or referrer.id == referee.id:
            return None, []

        existing = await session.execute(
            select(Referral).where(Referral.referee_id == referee.id)
        )
        if existing.scalar_one_or_none():
            return None, []

        session.add(Referral(referrer_id=referrer.id, referee_id=referee.id))

        now = datetime.utcnow()
        if referrer.referral_bonus_until and referrer.referral_bonus_until > now:
            referrer.referral_bonus_until += timedelta(hours=10)
        else:
            referrer.referral_bonus_until = now + timedelta(hours=10)

        count_result = await session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == referrer.id)
        )
        count = count_result.scalar() or 0

        milestones = []
        flags = referrer.ladder_rewarded or 0
        if count >= 3 and not (flags & 1):
            flags |= 1
            referrer.referral_bonus_until = (referrer.referral_bonus_until or now) + timedelta(days=7)
            milestones.append("3")

        if count >= 10 and not (flags & 2):
            flags |= 2
            milestones.append("10")

        if count >= 25 and not (flags & 4):
            flags |= 4
            sub = PremiumSubscription(
                user_id=referrer.id,
                end_date=now + timedelta(days=30),
            )
            session.add(sub)
            milestones.append("25")

        referrer.ladder_rewarded = flags
        await session.commit()
        return referrer, milestones


async def grant_premium_days(user_tg_id: int, days: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_tg_id))
        user = result.scalar_one_or_none()
        if user:
            session.add(PremiumSubscription(
                user_id=user.id,
                end_date=datetime.utcnow() + timedelta(days=days),
            ))
            await session.commit()


def user_can_see_whois(user: User) -> bool:
    if user.is_admin or user.is_developer:
        return True
    if user.premium_plus:
        return True
    if user.referral_bonus_until and user.referral_bonus_until > datetime.utcnow():
        return True
    return False


async def get_referral_count(telegram_id: int) -> int:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if not user:
            return 0
        count_result = await session.execute(
            select(func.count(Referral.id)).where(Referral.referrer_id == user.id)
        )
        return count_result.scalar() or 0


async def get_referral_leaderboard(limit: int = 10) -> list[tuple]:
    """Top referrers: (telegram_id, username, full_name, referrals_count)."""
    async with async_session() as session:
        result = await session.execute(
            select(
                User.telegram_id, User.username, User.full_name,
                func.count(Referral.id).label("cnt"),
            )
            .join(Referral, Referral.referrer_id == User.id)
            .group_by(User.id)
            .order_by(text("cnt DESC"))
            .limit(limit)
        )
        return [(row[0], row[1], row[2], row[3]) for row in result.all()]


# ───── Auto-delete old messages ─────

async def delete_old_messages(days: int) -> int:
    cutoff = datetime.utcnow() - timedelta(days=days)
    async with async_session() as session:
        result = await session.execute(
            delete(Message).where(Message.created_at < cutoff)
        )
        await session.commit()
        return result.rowcount


# ───── Broadcast ─────

# ───── Advert system ─────

async def get_advert_config() -> AdvertConfig:
    async with async_session() as session:
        result = await session.execute(select(AdvertConfig).limit(1))
        config = result.scalar_one_or_none()
        if not config:
            config = AdvertConfig()
            session.add(config)
            await session.commit()
            await session.refresh(config)
        return config


async def set_advert_interval(seconds: int):
    async with async_session() as session:
        result = await session.execute(select(AdvertConfig).limit(1))
        config = result.scalar_one_or_none()
        if not config:
            config = AdvertConfig(interval_seconds=seconds)
            session.add(config)
        else:
            config.interval_seconds = seconds
        await session.commit()


async def get_active_advert() -> Advert | None:
    async with async_session() as session:
        result = await session.execute(
            select(Advert).where(Advert.is_active == True).order_by(Advert.id.desc()).limit(1)
        )
        return result.scalar_one_or_none()


async def get_all_adverts() -> list[Advert]:
    async with async_session() as session:
        result = await session.execute(select(Advert).order_by(Advert.id.desc()))
        return list(result.scalars().all())


async def get_advert_by_id(advert_id: int) -> Advert | None:
    async with async_session() as session:
        result = await session.execute(select(Advert).where(Advert.id == advert_id))
        return result.scalar_one_or_none()


async def update_advert(advert_id: int, **kwargs):
    async with async_session() as session:
        result = await session.execute(select(Advert).where(Advert.id == advert_id))
        ad = result.scalar_one_or_none()
        if ad:
            for k, v in kwargs.items():
                setattr(ad, k, v)
            await session.commit()


async def delete_advert(advert_id: int):
    async with async_session() as session:
        await session.execute(delete(Advert).where(Advert.id == advert_id))
        await session.commit()


async def create_advert(
    name: str | None = None,
    text: str | None = None,
    photo_file_id: str | None = None,
    video_file_id: str | None = None,
    button_text: str | None = None,
    button_url: str | None = None,
) -> Advert:
    async with async_session() as session:
        ad = Advert(
            name=name,
            text=text,
            photo_file_id=photo_file_id,
            video_file_id=video_file_id,
            button_text=button_text,
            button_url=button_url,
        )
        session.add(ad)
        await session.commit()
        await session.refresh(ad)
        return ad


async def set_advert_enabled(enabled: bool):
    async with async_session() as session:
        result = await session.execute(select(AdvertConfig).limit(1))
        config = result.scalar_one_or_none()
        if not config:
            config = AdvertConfig(is_enabled=enabled)
            session.add(config)
        else:
            config.is_enabled = enabled
        await session.commit()


async def is_advert_enabled() -> bool:
    async with async_session() as session:
        result = await session.execute(select(AdvertConfig).limit(1))
        config = result.scalar_one_or_none()
        return bool(config and config.is_enabled)


# ───── Premium ─────

async def get_premium_plans() -> list[PremiumPlan]:
    async with async_session() as session:
        result = await session.execute(select(PremiumPlan).order_by(PremiumPlan.id))
        return list(result.scalars().all())


async def add_premium_plan(name: str, days: int, price: int) -> PremiumPlan:
    async with async_session() as session:
        plan = PremiumPlan(name=name, days=days, price=price)
        session.add(plan)
        await session.commit()
        await session.refresh(plan)
        return plan


async def remove_premium_plan(plan_id: int):
    async with async_session() as session:
        await session.execute(delete(PremiumPlan).where(PremiumPlan.id == plan_id))
        await session.commit()


async def set_premium(user_tg_id: int, plan_id: int) -> PremiumSubscription | None:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return None
        result = await session.execute(select(PremiumPlan).where(PremiumPlan.id == plan_id))
        plan = result.scalar_one_or_none()
        if not plan:
            return None
        sub = PremiumSubscription(
            user_id=user.id,
            end_date=datetime.utcnow() + timedelta(days=plan.days),
        )
        session.add(sub)
        await session.commit()
        await session.refresh(sub)
        return sub


async def remove_premium(user_tg_id: int):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_tg_id))
        user = result.scalar_one_or_none()
        if user:
            await session.execute(
                delete(PremiumSubscription).where(
                    PremiumSubscription.user_id == user.id,
                    PremiumSubscription.is_active == True,
                )
            )
            await session.commit()


async def is_premium(user_tg_id: int) -> bool:
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_tg_id))
        user = result.scalar_one_or_none()
        if not user:
            return False
        if user.premium_plus:
            return True
        result = await session.execute(
            select(PremiumSubscription).where(
                PremiumSubscription.user_id == user.id,
                PremiumSubscription.is_active == True,
                PremiumSubscription.end_date > datetime.utcnow(),
            ).limit(1)
        )
        return result.scalar_one_or_none() is not None


async def set_premium_plus(user_tg_id: int, on: bool):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == user_tg_id))
        user = result.scalar_one_or_none()
        if user:
            user.premium_plus = on
            await session.commit()


async def set_custom_greeting(telegram_id: int, text: str | None):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.custom_greeting = text
            await session.commit()


async def get_active_session_ids() -> list[int]:
    async with async_session() as session:
        result = await session.execute(select(ActiveSession.telegram_id))
        return [row[0] for row in result.all()]


# ───── Broadcast ─────

async def get_all_user_ids() -> list[int]:
    async with async_session() as session:
        result = await session.execute(select(User.telegram_id))
        return [row[0] for row in result.all()]


# ───── Export CSV ─────

async def export_messages_csv() -> str:
    async with async_session() as session:
        result = await session.execute(
            select(Message).order_by(Message.created_at)
        )
        msgs = result.scalars().all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["id", "link_id", "sender_id", "sender_username", "sender_full_name", "text", "created_at"])
    for m in msgs:
        writer.writerow([m.id, m.link_id, m.sender_id, m.sender_username, m.sender_full_name, m.text, m.created_at])
    return output.getvalue()
