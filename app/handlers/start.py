"""handlers/start.py — /start and /help commands."""

from telegram import Update
from telegram.ext import ContextTypes

from app.helpers import delete_later, delete_message

HELP_TEXT = """\
🤖 *DailyPilot* — your personal daily planner

*Task management*
/tasks — list all tasks
/add — add a new task
/edit — edit a task
/delete — delete a task

*Daily tracking*
/today — view today's plan
/update — update today's task statuses
/summary — today's results + score

*Progress*
/week — 7-day completion grid
/stats — 30-day analytics & streaks

*Journal*
/note — write today's daily note

*Settings*
/settings — view or change reminder times
/help — show this message
"""


async def cmd_start(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await delete_message(update.message)  # type: ignore[arg-type]
    msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
        "👋 Welcome to *DailyPilot*!\n\n"
        "I'll help you plan your day, track habits, and send you reminders.\n\n"
        "Type /help to see all commands.",
        parse_mode="Markdown",
    )
    delete_later(ctx, msg.chat_id, msg.message_id, delay=40)


async def cmd_help(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await delete_message(update.message)  # type: ignore[arg-type]
    msg = await update.effective_chat.send_message(HELP_TEXT, parse_mode="Markdown")  # type: ignore[union-attr]
    delete_later(ctx, msg.chat_id, msg.message_id, delay=40)
