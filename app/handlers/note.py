"""
handlers/note.py — /note command.

Saves or updates a short daily journal entry.

Flow
----
/note                  → show today's note (if exists) + [Edit] / [Clear] buttons
                         OR prompt immediately if no note exists
User types a note      → saved, bot message auto-deleted after 25 s
[Edit]                 → ask for new text
[Clear]                → delete today's note
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app import database as db
from app.helpers import delete_later, delete_message

NOTE_WRITE, NOTE_ACTION = range(2)
_CHAT, _MSG = "note_chat", "note_msg"


async def cmd_note(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_message(update.message)  # type: ignore[arg-type]
    existing = db.get_note()

    if existing:
        keyboard = InlineKeyboardMarkup([[
            InlineKeyboardButton("✏️ Edit", callback_data="note_edit"),
            InlineKeyboardButton("🗑️ Clear", callback_data="note_clear"),
            InlineKeyboardButton("✔️ Close", callback_data="note_close"),
        ]])
        msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
            f"📓 *Today's Note*\n\n_{existing['text']}_",
            parse_mode="Markdown",
            reply_markup=keyboard,
        )
        ctx.user_data[_CHAT] = msg.chat_id   # type: ignore[index]
        ctx.user_data[_MSG]  = msg.message_id # type: ignore[index]
        return NOTE_ACTION
    else:
        msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
            "📓 *Daily Note*\n\nWhat's on your mind today?",
            parse_mode="Markdown",
        )
        ctx.user_data[_CHAT] = msg.chat_id   # type: ignore[index]
        ctx.user_data[_MSG]  = msg.message_id # type: ignore[index]
        return NOTE_WRITE


async def note_action_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]

    if query.data == "note_close":  # type: ignore[union-attr]
        await query.edit_message_text("✔️ Note closed.")  # type: ignore[union-attr]
        delete_later(ctx, ctx.user_data[_CHAT], ctx.user_data[_MSG])  # type: ignore[index]
        return ConversationHandler.END

    if query.data == "note_clear":  # type: ignore[union-attr]
        db.save_note("")  # save empty — effectively clears it
        await query.edit_message_text("🗑️ Note cleared.")  # type: ignore[union-attr]
        delete_later(ctx, ctx.user_data[_CHAT], ctx.user_data[_MSG])  # type: ignore[index]
        return ConversationHandler.END

    # note_edit
    await query.edit_message_text(  # type: ignore[union-attr]
        "📓 Write your updated note:", parse_mode="Markdown"
    )
    return NOTE_WRITE


async def note_write_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()  # type: ignore[union-attr]
    await delete_message(update.message)  # type: ignore[arg-type]

    if not text:
        await ctx.bot.edit_message_text(
            chat_id=ctx.user_data[_CHAT],   # type: ignore[index]
            message_id=ctx.user_data[_MSG], # type: ignore[index]
            text="⚠️ Note can't be empty. Try again:",
        )
        return NOTE_WRITE

    db.save_note(text)
    await ctx.bot.edit_message_text(
        chat_id=ctx.user_data[_CHAT],   # type: ignore[index]
        message_id=ctx.user_data[_MSG], # type: ignore[index]
        text=f"📓 *Note saved!*\n\n_{text}_",
        parse_mode="Markdown",
    )
    delete_later(ctx, ctx.user_data[_CHAT], ctx.user_data[_MSG])  # type: ignore[index]
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_message(update.message)  # type: ignore[arg-type]
    await ctx.bot.edit_message_text(
        chat_id=ctx.user_data[_CHAT],   # type: ignore[index]
        message_id=ctx.user_data[_MSG], # type: ignore[index]
        text="❌ Cancelled.",
    )
    delete_later(ctx, ctx.user_data[_CHAT], ctx.user_data[_MSG])  # type: ignore[index]
    return ConversationHandler.END


note_conversation = ConversationHandler(
    entry_points=[CommandHandler("note", cmd_note)],
    states={
        NOTE_ACTION: [CallbackQueryHandler(note_action_cb, pattern="^note_")],
        NOTE_WRITE:  [MessageHandler(filters.TEXT & ~filters.COMMAND, note_write_msg)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
)
