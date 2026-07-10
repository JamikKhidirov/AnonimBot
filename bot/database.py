import secrets
import csv
import io
from datetime import datetime, timedelta

from sqlalchemy import (
    Column, Integer, BigInteger, String, Text, Boolean,
    DateTime, ForeignKey, select, delete, func, or_, text,
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
    created_at = Column(DateTime, default=datetime.utcnow)

    links = relationship("ChatLink", back_populates="user")


class ChatLink(Base):
    __tablename__ = "chat_links"

    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    code = Column(String(64), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)
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
    text = Column(Text, nullable=False)
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


engine = create_async_engine(DATABASE_URL)
async_session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # ── Migration: add missing columns for existing DBs ──
    migrations = [
        ("users", "language", "VARCHAR(5) DEFAULT 'ru'"),
        ("forwarded_messages", "reply_text", "TEXT"),
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


async def get_or_create_user(telegram_id: int, username: str | None, full_name: str | None) -> User:
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
        if telegram_id == DEVELOPER_ID:
            user.is_developer = True
            user.is_admin = True
        session.add(user)
        await session.commit()
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
        await session.refresh(link)
        return link


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


async def create_message(
    link_id: int, sender_id: int, text: str,
    sender_username: str | None = None, sender_full_name: str | None = None,
) -> Message:
    async with async_session() as session:
        msg = Message(
            link_id=link_id,
            sender_id=sender_id,
            sender_username=sender_username,
            sender_full_name=sender_full_name,
            text=text,
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

async def set_user_language(telegram_id: int, lang: str):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.telegram_id == telegram_id))
        user = result.scalar_one_or_none()
        if user:
            user.language = lang
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
