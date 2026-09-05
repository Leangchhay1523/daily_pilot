"""
bot.py — DailyPilot entry point.

Run with:
    python -m app.bot
"""

import logging
import os

from telegram import Update
from telegram.ext import Application, CommandHandler

from app import config, database as db
from app.handlers.start import cmd_start, cmd_help
from app.handlers.tasks import add_conversation, edit_conversation, delete_conversation, cmd_tasks
from app.handlers.daily import today_handler, update_handler, update_cb_handler
from app.handlers.summary import summary_handler
from app.handlers.weekly import week_handler
from app.handlers.note import note_conversation
from app.handlers.stats import stats_handler
from app.handlers.settings import settings_conversation
from app.scheduler import create_scheduler

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
)
log = logging.getLogger(__name__)

CHAT_ID: int | None = int(os.environ["CHAT_ID"]) if os.environ.get("CHAT_ID") else None


async def post_init(app: Application) -> None:
    db.init_db()
    log.info("Database initialised.")

    chat_id = app.bot_data.get("chat_id") or CHAT_ID
    if chat_id:
        scheduler = create_scheduler(app.bot, chat_id)
        scheduler.start()
        app.bot_data["scheduler"] = scheduler
        log.info("Scheduler started (chat_id=%s).", chat_id)
    else:
        log.warning(
            "No CHAT_ID set. Send /start to the bot to enable scheduled reminders."
        )


async def cmd_start_with_scheduler(update: Update, ctx) -> None:
    chat_id = update.effective_chat.id  # type: ignore[union-attr]
    if "scheduler" not in ctx.bot_data:
        ctx.bot_data["chat_id"] = chat_id
        scheduler = create_scheduler(ctx.bot, chat_id)
        scheduler.start()
        ctx.bot_data["scheduler"] = scheduler
        log.info("Scheduler started lazily for chat_id=%s", chat_id)
    await cmd_start(update, ctx)


def main() -> None:
    app = (
        Application.builder()
        .token(config.BOT_TOKEN)
        .post_init(post_init)
        .build()
    )

    # Core
    app.add_handler(CommandHandler("start", cmd_start_with_scheduler))
    app.add_handler(CommandHandler("help",  cmd_help))
    app.add_handler(CommandHandler("tasks", cmd_tasks))

    # Task management conversations
    app.add_handler(add_conversation)
    app.add_handler(edit_conversation)
    app.add_handler(delete_conversation)

    # Daily tracking
    app.add_handler(today_handler)
    app.add_handler(update_handler)
    app.add_handler(update_cb_handler)

    # New features
    app.add_handler(summary_handler)   # /summary
    app.add_handler(week_handler)      # /week
    app.add_handler(note_conversation) # /note
    app.add_handler(stats_handler)     # /stats

    # Settings
    app.add_handler(settings_conversation)

    log.info("DailyPilot starting…")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
