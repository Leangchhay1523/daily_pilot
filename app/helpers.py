"""
helpers.py — Shared utilities for DailyPilot handlers.

Auto-delete flow
----------------
- User command messages  → deleted immediately.
- Bot interaction messages → scheduled for deletion after a delay.
- Scheduled notifications → NEVER deleted (morning / evening).
"""

import logging
from telegram import Message
from telegram.error import TelegramError
from telegram.ext import ContextTypes

log = logging.getLogger(__name__)

# How many seconds before a temporary bot message disappears
TEMP_DELETE_DELAY: float = 30   # default (short responses)
LONG_DELETE_DELAY: float = 120  # interactive panels (/update)


async def _delete_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Job callback — silently deletes a message."""
    data = context.job.data  # type: ignore[union-attr]
    try:
        await context.bot.delete_message(
            chat_id=data["chat_id"],
            message_id=data["message_id"],
        )
    except TelegramError:
        pass  # message already deleted or too old — ignore


def delete_later(
    ctx: ContextTypes.DEFAULT_TYPE,
    chat_id: int,
    message_id: int,
    delay: float = TEMP_DELETE_DELAY,
) -> None:
    """Schedule *message_id* in *chat_id* to be deleted after *delay* seconds."""
    ctx.job_queue.run_once(  # type: ignore[union-attr]
        _delete_job,
        delay,
        data={"chat_id": chat_id, "message_id": message_id},
    )


async def delete_message(message: Message) -> None:
    """Silently delete a Telegram message (swallows all errors)."""
    try:
        await message.delete()
    except TelegramError:
        pass
