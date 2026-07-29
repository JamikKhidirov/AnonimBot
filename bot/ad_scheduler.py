import asyncio
import json
import logging
from datetime import datetime

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from bot import bot
from bot.database import (
    get_advert_config, get_active_advert, get_active_session_ids, is_premium,
)

logger = logging.getLogger(__name__)


async def _send_ad(telegram_id: int, ad):
    if not ad or not ad.is_active:
        return

    kb = None
    if ad.buttons_json:
        try:
            buttons = json.loads(ad.buttons_json)
            kb = InlineKeyboardMarkup(inline_keyboard=[
                [InlineKeyboardButton(text=b["text"], url=b["url"])] for b in buttons
            ])
        except Exception:
            pass

    try:
        if ad.video_file_id:
            await bot.send_video(telegram_id, ad.video_file_id, caption=ad.text or "", reply_markup=kb)
        elif ad.text:
            await bot.send_message(telegram_id, ad.text, reply_markup=kb)
    except Exception as e:
        logger.debug(f"Failed to send ad to {telegram_id}: {e}")


async def ad_scheduler():
    await asyncio.sleep(10)
    logger.info("Ad scheduler started")
    while True:
        try:
            config = await get_advert_config()
            now = datetime.utcnow()

            last = config.last_sent_at
            if last and (now - last).total_seconds() < config.interval_seconds:
                await asyncio.sleep(30)
                continue

            ad = await get_active_advert()
            if not ad:
                await asyncio.sleep(30)
                continue

            session_ids = await get_active_session_ids()
            for tg_id in session_ids:
                if await is_premium(tg_id):
                    continue
                await _send_ad(tg_id, ad)
                await asyncio.sleep(0.05)

            config.last_sent_at = now
            from bot.database import async_session, select, AdvertConfig
            async with async_session() as session:
                result = await session.execute(select(AdvertConfig).limit(1))
                c = result.scalar_one_or_none()
                if c:
                    c.last_sent_at = now
                    await session.commit()

            logger.info(f"Ad sent to {len(session_ids)} users")
        except Exception as e:
            logger.exception(f"Ad scheduler error: {e}")

        await asyncio.sleep(30)
