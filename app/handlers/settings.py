"""
handlers/settings.py

/settings — view and change reminder times.

Clean-chat strategy: single bot message, edited in place, auto-deleted after 25 s.
"""

import re
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import (
    CallbackQueryHandler,
    CommandHandler,
    ContextTypes,
    ConversationHandler,
    MessageHandler,
    filters,
)

from app.helpers import delete_later, delete_message

# States
SETTINGS_MAIN, SETTINGS_MORNING, SETTINGS_EVENING = range(3)

_TIME_RE = re.compile(r"^(\d{1,2}):(\d{2})$")

_CHAT = "set_chat_id"
_MSG  = "set_msg_id"


def _settings_text(ctx: ContextTypes.DEFAULT_TYPE) -> str:
    m_h = ctx.bot_data.get("morning_hour", 9)
    m_m = ctx.bot_data.get("morning_minute", 0)
    e_h = ctx.bot_data.get("evening_hour", 21)
    e_m = ctx.bot_data.get("evening_minute", 0)
    return (
        f"⚙️ *Settings*\n\n"
        f"🌅 Morning reminder: `{m_h:02d}:{m_m:02d}`\n"
        f"🌙 Evening check-in: `{e_h:02d}:{e_m:02d}`\n"
    )


def _settings_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("🌅 Change morning", callback_data="set_morning"),
            InlineKeyboardButton("🌙 Change evening", callback_data="set_evening"),
        ],
        [InlineKeyboardButton("✔️ Close", callback_data="set_close")],
    ])


async def _edit(ctx, text, keyboard=None, **kw):
    await ctx.bot.edit_message_text(
        chat_id=ctx.user_data[_CHAT],   # type: ignore[index]
        message_id=ctx.user_data[_MSG], # type: ignore[index]
        text=text,
        reply_markup=keyboard,
        **kw,
    )


async def cmd_settings(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_message(update.message)  # type: ignore[arg-type]
    msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
        _settings_text(ctx),
        parse_mode="Markdown",
        reply_markup=_settings_keyboard(),
    )
    ctx.user_data[_CHAT] = msg.chat_id    # type: ignore[index]
    ctx.user_data[_MSG]  = msg.message_id # type: ignore[index]
    return SETTINGS_MAIN


async def settings_main_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]

    if query.data == "set_close":  # type: ignore[union-attr]
        await query.edit_message_text("✔️ Settings closed.")  # type: ignore[union-attr]
        delete_later(ctx, ctx.user_data[_CHAT], ctx.user_data[_MSG])  # type: ignore[index]
        return ConversationHandler.END

    if query.data == "set_morning":  # type: ignore[union-attr]
        await query.edit_message_text(  # type: ignore[union-attr]
            "🌅 Enter new morning reminder time in `HH:MM` (24-hour):",
            parse_mode="Markdown",
        )
        ctx.user_data["set_target"] = "morning"  # type: ignore[index]
        return SETTINGS_MORNING

    await query.edit_message_text(  # type: ignore[union-attr]
        "🌙 Enter new evening check-in time in `HH:MM` (24-hour):",
        parse_mode="Markdown",
    )
    ctx.user_data["set_target"] = "evening"  # type: ignore[index]
    return SETTINGS_EVENING


async def settings_time_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    text = update.message.text.strip()  # type: ignore[union-attr]
    await delete_message(update.message)  # type: ignore[arg-type]

    target = ctx.user_data.get("set_target", "morning")  # type: ignore[index]

    m = _TIME_RE.match(text)
    if not m:
        await _edit(
            ctx,
            "❌ Invalid format. Please use `HH:MM`, e.g. `09:00`.",
            parse_mode="Markdown",
        )
        return SETTINGS_MORNING if target == "morning" else SETTINGS_EVENING

    hour, minute = int(m.group(1)), int(m.group(2))
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        await _edit(ctx, "❌ Invalid time. Hour 0–23, minute 0–59.")
        return SETTINGS_MORNING if target == "morning" else SETTINGS_EVENING

    if target == "morning":
        ctx.bot_data["morning_hour"]   = hour
        ctx.bot_data["morning_minute"] = minute
        label = "🌅 Morning reminder"
    else:
        ctx.bot_data["evening_hour"]   = hour
        ctx.bot_data["evening_minute"] = minute
        label = "🌙 Evening check-in"

    ctx.bot_data["reschedule"] = True

    await _edit(
        ctx,
        f"✅ {label} set to `{hour:02d}:{minute:02d}`.\n"
        "_Restart the bot for the change to take effect._",
        parse_mode="Markdown",
    )
    delete_later(ctx, ctx.user_data[_CHAT], ctx.user_data[_MSG])  # type: ignore[index]
    return ConversationHandler.END


async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_message(update.message)  # type: ignore[arg-type]
    await _edit(ctx, "❌ Cancelled.")
    delete_later(ctx, ctx.user_data[_CHAT], ctx.user_data[_MSG])  # type: ignore[index]
    return ConversationHandler.END


settings_conversation = ConversationHandler(
    entry_points=[CommandHandler("settings", cmd_settings)],
    states={
        SETTINGS_MAIN:    [CallbackQueryHandler(settings_main_cb, pattern="^set_")],
        SETTINGS_MORNING: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_time_msg)],
        SETTINGS_EVENING: [MessageHandler(filters.TEXT & ~filters.COMMAND, settings_time_msg)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
)
