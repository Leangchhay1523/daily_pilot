"""
handlers/daily.py

/today  — send today's plan (auto-deletes after 60 s)
/update — interactive status editor in a single message (auto-deletes when done)

Persistent messages (morning/evening scheduler) are NOT generated here.
"""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import CallbackQueryHandler, CommandHandler, ContextTypes

from app import database as db
from app.helpers import delete_later, delete_message, LONG_DELETE_DELAY

STATUS_EMOJI = {
    "done":        "✅",
    "partial":     "🔶",
    "skipped":     "⏭️",
    "not_started": "☐",
}


# ── /today ─────────────────────────────────────────────────────────────────────

def _build_today_text() -> str:
    db.ensure_daily_records()
    records = db.get_daily_records()
    if not records:
        return "📋 No active tasks for today.\nUse /add to create some tasks first."
    lines = ["📅 *Today's Plan*\n"]
    for r in records:
        emoji = STATUS_EMOJI.get(r["status"], "☐")
        lines.append(f"{emoji} {r['name']} — {r['duration']}")
    return "\n".join(lines)


async def cmd_today(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Send today's plan — auto-deletes after 60 s."""
    await delete_message(update.message)  # type: ignore[arg-type]
    text = _build_today_text()
    msg = await update.effective_chat.send_message(text, parse_mode="Markdown")  # type: ignore[union-attr]
    delete_later(ctx, msg.chat_id, msg.message_id, delay=60)


# ── /update ────────────────────────────────────────────────────────────────────

def _build_update_keyboard(records) -> InlineKeyboardMarkup:
    rows = []
    for r in records:
        rows.append([
            InlineKeyboardButton(
                f"{'✅' if r['status'] == 'done'    else '⬜'} Done",
                callback_data=f"set_{r['id']}_done",
            ),
            InlineKeyboardButton(
                f"{'🔶' if r['status'] == 'partial' else '⬜'} Partial",
                callback_data=f"set_{r['id']}_partial",
            ),
            InlineKeyboardButton(
                f"{'⏭️' if r['status'] == 'skipped' else '⬜'} Skip",
                callback_data=f"set_{r['id']}_skipped",
            ),
        ])
    rows.append([InlineKeyboardButton("✔️ Done updating", callback_data="update_done")])
    return InlineKeyboardMarkup(rows)


def _build_update_text(records) -> str:
    lines = ["📝 *Today's Progress*\n"]
    for r in records:
        emoji = STATUS_EMOJI.get(r["status"], "☐")
        lines.append(f"{emoji} *{r['name']}* — {r['duration']}")
    return "\n".join(lines)


async def cmd_update(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Open the interactive task-status panel."""
    await delete_message(update.message)  # type: ignore[arg-type]
    db.ensure_daily_records()
    records = db.get_daily_records()
    if not records:
        msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
            "📋 No active tasks for today. Use /add to create some."
        )
        delete_later(ctx, msg.chat_id, msg.message_id)
        return

    text     = _build_update_text(records)
    keyboard = _build_update_keyboard(records)
    msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
        text, parse_mode="Markdown", reply_markup=keyboard
    )
    # Store so callback can reference it for eventual deletion
    ctx.user_data["update_chat_id"] = msg.chat_id   # type: ignore[index]
    ctx.user_data["update_msg_id"]  = msg.message_id  # type: ignore[index]
    # Safety: auto-delete after 2 minutes if user never taps "Done"
    delete_later(ctx, msg.chat_id, msg.message_id, delay=LONG_DELETE_DELAY)


async def update_status_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle [Done / Partial / Skip] and [Done updating] button presses."""
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]

    if query.data == "update_done":  # type: ignore[union-attr]
        summary = db.daily_summary()
        total   = summary["total"]
        done    = summary["done"]
        partial = summary["partial"]
        skipped = summary["skipped"]
        await query.edit_message_text(  # type: ignore[union-attr]
            f"✅ *Progress saved!*\n\n"
            f"✅ Done: {done}/{total}\n"
            f"🔶 Partial: {partial}/{total}\n"
            f"⏭️ Skipped: {skipped}/{total}",
            parse_mode="Markdown",
        )
        # Cancel the safety timer (if still pending) and delete immediately
        delete_later(ctx, query.message.chat_id, query.message.message_id, delay=8)  # type: ignore[union-attr]
        return

    # parse callback: "set_<record_id>_<status>"
    _, record_id_str, status = query.data.split("_", 2)  # type: ignore[union-attr]
    db.set_record_status(int(record_id_str), status)

    records  = db.get_daily_records()
    text     = _build_update_text(records)
    keyboard = _build_update_keyboard(records)
    await query.edit_message_text(text, parse_mode="Markdown", reply_markup=keyboard)  # type: ignore[union-attr]


# Handlers to register
today_handler     = CommandHandler("today", cmd_today)
update_handler    = CommandHandler("update", cmd_update)
update_cb_handler = CallbackQueryHandler(
    update_status_cb,
    pattern=r"^(set_\d+_(done|partial|skipped)|update_done)$",
)
