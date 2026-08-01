import asyncio
import logging
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot
from bot.database import (
    get_advert_config, get_active_advert, get_all_user_ids, is_premium, is_banned,
    get_advert_by_id, async_session, select, AdvertConfig,
)

logger = logging.getLogger(__name__)


async def _send_ad(telegram_id: int, ad) -> tuple[bool, str]:
    """Send ad to one user. Returns (success, error_reason_or_empty)."""
    if not ad:
        return False, "ad not found"

    kb = None
    if ad.button_text and ad.button_url:
        kb = InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text=ad.button_text, url=ad.button_url)],
        ])

    caption = ad.text or ""
    try:
        if ad.video_file_id:
            await bot.send_video(telegram_id, ad.video_file_id, caption=caption, reply_markup=kb, parse_mode=None)
        elif ad.photo_file_id:
            await bot.send_photo(telegram_id, ad.photo_file_id, caption=caption, reply_markup=kb, parse_mode=None)
        elif ad.text:
            await bot.send_message(telegram_id, ad.text, reply_markup=kb, parse_mode=None)
        else:
            return False, "ad has no text and no media"
        return True, ""
    except Exception as e:
        reason = f"{type(e).__name__}: {e}"
        logger.warning(f"Ad send FAILED -> user {telegram_id}: {reason}")
        return False, reason


async def _update_last_sent(now: datetime):
    try:
        async with async_session() as session:
            result = await session.execute(select(AdvertConfig).limit(1))
            c = result.scalar_one_or_none()
            if c:
                c.last_sent_at = now
                await session.commit()
    except Exception as e:
        logger.exception(f"Failed to update last_sent_at: {e}")


async def send_ad_now(ad_id: int) -> dict:
    """Send ad to all users. Returns breakdown dict with error reasons."""
    ad = await get_advert_by_id(ad_id)
    if not ad:
        logger.warning(f"send_ad_now: ad {ad_id} not found")
        return {"sent": 0, "total": 0, "skipped": 0, "errors": {}}

    user_ids = await get_all_user_ids()
    sent = 0
    skipped = 0
    errors: dict[str, int] = {}
    for tg_id in user_ids:
        try:
            if await is_premium(tg_id):
                skipped += 1
                continue
            if await is_banned(tg_id):
                skipped += 1
                continue
            ok, reason = await _send_ad(tg_id, ad)
            if ok:
                sent += 1
            else:
                errors[reason] = errors.get(reason, 0) + 1
        except Exception as e:
            reason = f"{type(e).__name__}: {e}"
            errors[reason] = errors.get(reason, 0) + 1
        await asyncio.sleep(0.05)

    logger.info(f"send_ad_now(ad={ad_id}): sent={sent} total={len(user_ids)} skipped={skipped} errors={sum(errors.values())}")
    for reason, count in errors.items():
        logger.warning(f"  ad error reason [{count}x]: {reason}")
    return {"sent": sent, "total": len(user_ids), "skipped": skipped, "errors": errors}


async def send_active_ad_now() -> dict:
    ad = await get_active_advert()
    if not ad:
        return {"sent": 0, "total": 0, "skipped": 0, "errors": {"no active ad": 1}}
    return await send_ad_now(ad.id)


async def ad_scheduler():
    await asyncio.sleep(10)
    logger.info("Ad scheduler started")
    while True:
        try:
            config = await get_advert_config()
            if not config.is_enabled:
                await asyncio.sleep(30)
                continue

            now = datetime.utcnow()
            last = config.last_sent_at
            if last and (now - last).total_seconds() < config.interval_seconds:
                await asyncio.sleep(30)
                continue

            ad = await get_active_advert()
            if not ad:
                await asyncio.sleep(30)
                continue

            user_ids = await get_all_user_ids()
            sent = 0
            errors: dict[str, int] = {}
            for tg_id in user_ids:
                try:
                    if await is_premium(tg_id):
                        continue
                    if await is_banned(tg_id):
                        continue
                    ok, reason = await _send_ad(tg_id, ad)
                    if ok:
                        sent += 1
                    else:
                        errors[reason] = errors.get(reason, 0) + 1
                except Exception as e:
                    reason = f"{type(e).__name__}: {e}"
                    errors[reason] = errors.get(reason, 0) + 1
                await asyncio.sleep(0.05)

            await _update_last_sent(now)
            logger.info(f"Ad '{ad.name or ad.id}' sent to {sent} users (errors: {sum(errors.values())})")
            for reason, count in errors.items():
                logger.warning(f"  ad error reason [{count}x]: {reason}")
        except Exception as e:
            logger.exception(f"Ad scheduler error: {e}")

        await asyncio.sleep(30)
