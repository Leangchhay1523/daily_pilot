"""
scheduler.py — APScheduler-based background job runner.

Jobs
----
morning_reminder  — sends today's plan at 09:00
evening_checkin   — sends end-of-day check-in prompt at 21:00
"""

import logging
from datetime import date

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from telegram import Bot, InlineKeyboardButton, InlineKeyboardMarkup

from app import database as db
from app import config

log = logging.getLogger(__name__)

STATUS_EMOJI = {
    "done":        "✅",
    "partial":     "🔶",
    "skipped":     "⏭️",
    "not_started": "☐",
}


async def send_morning_reminder(bot: Bot, chat_id: int) -> None:
    """Persistent 9 AM plan message."""
    db.ensure_daily_records()
    records = db.get_daily_records()
    streaks = db.get_all_streaks()

    if not records:
        text = (
            "🌅 *Good morning!*\n\n"
            "📋 You have no active tasks today.\n"
            "Use /add to set up your habits."
        )
    else:
        lines = ["🌅 *Good morning!*\n\n📅 *Today's Plan*\n"]
        for i, r in enumerate(records, 1):
            s = streaks.get(r["task_id"], 0)
            streak_txt = f"  🔥 {s}" if s >= 2 else ""
            lines.append(f"{i}. {r['name']} — {r['duration']}{streak_txt}")
        text = "\n".join(lines)

    await bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
    log.info("Morning reminder sent to %s", chat_id)



async def send_evening_checkin(bot: Bot, chat_id: int) -> None:
    """Persistent evening check-in message."""
    summary = db.daily_summary()
    total = summary["total"]

    if total == 0:
        await bot.send_message(
            chat_id=chat_id,
            text="🌙 *Evening Check-In*\n\nNo tasks recorded today.",
            parse_mode="Markdown",
        )
        return

    done = summary["done"] + summary["partial"]
    not_done = summary["not_started"]

    keyboard = InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📝 Update Status", switch_inline_query_current_chat="/update"),
            InlineKeyboardButton("📋 View Today", switch_inline_query_current_chat="/today"),
        ]
    ])

    text = (
        f"🌙 *Daily Check-In*\n\n"
        f"How did you do today?\n\n"
        f"✅ Completed: {done}/{total}\n"
        f"☐ Not started: {not_done}/{total}"
    )
    if not_done > 0:
        text += "\n\n_You haven't finished updating today's tasks._"

    await bot.send_message(
        chat_id=chat_id,
        text=text,
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    log.info("Evening check-in sent to %s", chat_id)


def create_scheduler(bot: Bot, chat_id: int) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()

    scheduler.add_job(
        send_morning_reminder,
        trigger=CronTrigger(hour=config.MORNING_HOUR, minute=config.MORNING_MINUTE),
        args=[bot, chat_id],
        id="morning_reminder",
        replace_existing=True,
    )

    scheduler.add_job(
        send_evening_checkin,
        trigger=CronTrigger(hour=config.EVENING_HOUR, minute=config.EVENING_MINUTE),
        args=[bot, chat_id],
        id="evening_checkin",
        replace_existing=True,
    )

    return scheduler
