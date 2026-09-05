"""
handlers/tasks.py

Task management — /tasks /add /edit /delete

Clean-chat strategy
-------------------
- Every user command message is deleted immediately.
- Multi-step conversations maintain **one** bot message that is edited in place.
- The final bot message is scheduled for auto-deletion after 25 s.
- User text replies inside conversations are deleted immediately.
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
from app.helpers import delete_later, delete_message, TEMP_DELETE_DELAY

# ── Conversation states ────────────────────────────────────────────────────────
(
    ADD_NAME,
    ADD_DURATION,
    ADD_CONFIRM,
    EDIT_PICK,
    EDIT_FIELD,
    EDIT_VALUE,
    DELETE_PICK,
    DELETE_CONFIRM,
) = range(8)

# shorthand keys stored in user_data
_CHAT = "conv_chat_id"
_MSG  = "conv_msg_id"


async def _edit(ctx: ContextTypes.DEFAULT_TYPE, text: str, keyboard=None, **kw):
    """Edit the single conversation message stored in user_data."""
    await ctx.bot.edit_message_text(
        chat_id=ctx.user_data[_CHAT],  # type: ignore[index]
        message_id=ctx.user_data[_MSG],  # type: ignore[index]
        text=text,
        reply_markup=keyboard,
        **kw,
    )


def _schedule_end(ctx: ContextTypes.DEFAULT_TYPE):
    """Schedule the conversation message for deletion."""
    delete_later(ctx, ctx.user_data[_CHAT], ctx.user_data[_MSG])  # type: ignore[index]


# ── /tasks ─────────────────────────────────────────────────────────────────────

def _task_list_text() -> str:
    tasks = db.get_all_tasks()
    if not tasks:
        return "📋 You have no tasks yet. Use /add to create one."
    lines = ["📋 *Your Tasks*\n"]
    for t in tasks:
        icon = "🟢" if t["active"] else "🔴"
        lines.append(f"{icon} *{t['name']}* — {t['duration']}")
    return "\n".join(lines)


async def cmd_tasks(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await delete_message(update.message)  # type: ignore[arg-type]
    msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
        _task_list_text(), parse_mode="Markdown"
    )
    delete_later(ctx, msg.chat_id, msg.message_id)


# ── /add ──────────────────────────────────────────────────────────────────────

async def cmd_add(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()  # type: ignore[union-attr]
    await delete_message(update.message)  # type: ignore[arg-type]
    msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
        "➕ *Add a new task*\n\nWhat's the name of the task?",
        parse_mode="Markdown",
    )
    ctx.user_data[_CHAT] = msg.chat_id  # type: ignore[index]
    ctx.user_data[_MSG]  = msg.message_id  # type: ignore[index]
    return ADD_NAME


async def add_got_name(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    name = update.message.text.strip()  # type: ignore[union-attr]
    await delete_message(update.message)  # type: ignore[arg-type]
    if not name:
        await _edit(ctx, "⚠️ Please enter a valid name.")
        return ADD_NAME
    ctx.user_data["add_name"] = name  # type: ignore[index]
    await _edit(
        ctx,
        f"📝 Task: *{name}*\n\nHow long does this take?\n_(e.g. `2 hours`, `30 minutes`, `1h 30m`)_",
        parse_mode="Markdown",
    )
    return ADD_DURATION


async def add_got_duration(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    duration = update.message.text.strip()  # type: ignore[union-attr]
    await delete_message(update.message)  # type: ignore[arg-type]
    if not duration:
        await _edit(ctx, "⚠️ Please enter a duration.")
        return ADD_DURATION
    ctx.user_data["add_duration"] = duration  # type: ignore[index]
    name = ctx.user_data["add_name"]  # type: ignore[index]
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Confirm", callback_data="add_confirm"),
        InlineKeyboardButton("❌ Cancel",  callback_data="add_cancel"),
    ]])
    await _edit(
        ctx,
        f"*Confirm new task?*\n\n📌 Name: *{name}*\n⏱️ Duration: *{duration}*",
        keyboard=keyboard,
        parse_mode="Markdown",
    )
    return ADD_CONFIRM


async def add_confirm_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    if query.data == "add_confirm":  # type: ignore[union-attr]
        name     = ctx.user_data["add_name"]  # type: ignore[index]
        duration = ctx.user_data["add_duration"]  # type: ignore[index]
        db.add_task(name, duration)
        await query.edit_message_text(f"✅ *{name}* added!", parse_mode="Markdown")  # type: ignore[union-attr]
    else:
        await query.edit_message_text("❌ Cancelled.")  # type: ignore[union-attr]
    _schedule_end(ctx)
    return ConversationHandler.END


# ── /edit ─────────────────────────────────────────────────────────────────────

async def cmd_edit(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()  # type: ignore[union-attr]
    await delete_message(update.message)  # type: ignore[arg-type]
    tasks = db.get_all_tasks()
    if not tasks:
        msg = await update.effective_chat.send_message("You have no tasks to edit.")  # type: ignore[union-attr]
        delete_later(ctx, msg.chat_id, msg.message_id)
        return ConversationHandler.END

    buttons = [
        [InlineKeyboardButton(
            f"{'🟢' if t['active'] else '🔴'} {t['name']} ({t['duration']})",
            callback_data=f"edit_pick_{t['id']}",
        )]
        for t in tasks
    ]
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="edit_cancel")])
    msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
        "✏️ *Edit a task* — pick one:",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    ctx.user_data[_CHAT] = msg.chat_id  # type: ignore[index]
    ctx.user_data[_MSG]  = msg.message_id  # type: ignore[index]
    return EDIT_PICK


async def edit_pick_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    if query.data == "edit_cancel":  # type: ignore[union-attr]
        await query.edit_message_text("❌ Cancelled.")  # type: ignore[union-attr]
        _schedule_end(ctx)
        return ConversationHandler.END

    task_id = int(query.data.split("_")[-1])  # type: ignore[union-attr]
    task = db.get_task(task_id)
    ctx.user_data["edit_task_id"] = task_id  # type: ignore[index]
    ctx.user_data["edit_task"]    = dict(task)  # type: ignore[index]

    active_label = "🟢 Active" if task["active"] else "🔴 Inactive"
    buttons = InlineKeyboardMarkup([
        [InlineKeyboardButton("📝 Name",          callback_data="ef_name"),
         InlineKeyboardButton("⏱️ Duration",      callback_data="ef_duration")],
        [InlineKeyboardButton("🔁 Toggle active", callback_data="ef_toggle")],
        [InlineKeyboardButton("❌ Cancel",         callback_data="ef_cancel")],
    ])
    await query.edit_message_text(  # type: ignore[union-attr]
        f"✏️ Editing: *{task['name']}*\n"
        f"Duration: {task['duration']} | {active_label}\n\n"
        "What do you want to change?",
        parse_mode="Markdown",
        reply_markup=buttons,
    )
    return EDIT_FIELD


async def edit_field_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]

    if query.data == "ef_cancel":  # type: ignore[union-attr]
        await query.edit_message_text("❌ Cancelled.")  # type: ignore[union-attr]
        _schedule_end(ctx)
        return ConversationHandler.END

    if query.data == "ef_toggle":  # type: ignore[union-attr]
        task     = ctx.user_data["edit_task"]  # type: ignore[index]
        new_active = not bool(task["active"])
        db.update_task(task["id"], active=new_active)
        label = "activated 🟢" if new_active else "deactivated 🔴"
        await query.edit_message_text(  # type: ignore[union-attr]
            f"*{task['name']}* has been {label}.", parse_mode="Markdown"
        )
        _schedule_end(ctx)
        return ConversationHandler.END

    ctx.user_data["edit_field"] = query.data  # type: ignore[index]
    field_name = "name" if query.data == "ef_name" else "duration"  # type: ignore[union-attr]
    await query.edit_message_text(f"✏️ Enter new *{field_name}*:", parse_mode="Markdown")  # type: ignore[union-attr]
    return EDIT_VALUE


async def edit_value_msg(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    value   = update.message.text.strip()  # type: ignore[union-attr]
    await delete_message(update.message)  # type: ignore[arg-type]
    task_id = ctx.user_data["edit_task_id"]  # type: ignore[index]
    field   = ctx.user_data["edit_field"]  # type: ignore[index]

    if field == "ef_name":
        db.update_task(task_id, name=value)
        await _edit(ctx, f"✅ Name updated to *{value}*.", parse_mode="Markdown")
    else:
        db.update_task(task_id, duration=value)
        await _edit(ctx, f"✅ Duration updated to *{value}*.", parse_mode="Markdown")

    _schedule_end(ctx)
    return ConversationHandler.END


# ── /delete ───────────────────────────────────────────────────────────────────

async def cmd_delete(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    ctx.user_data.clear()  # type: ignore[union-attr]
    await delete_message(update.message)  # type: ignore[arg-type]
    tasks = db.get_all_tasks()
    if not tasks:
        msg = await update.effective_chat.send_message("You have no tasks to delete.")  # type: ignore[union-attr]
        delete_later(ctx, msg.chat_id, msg.message_id)
        return ConversationHandler.END

    buttons = [
        [InlineKeyboardButton(
            f"🗑️ {t['name']} ({t['duration']})",
            callback_data=f"del_pick_{t['id']}",
        )]
        for t in tasks
    ]
    buttons.append([InlineKeyboardButton("❌ Cancel", callback_data="del_cancel")])
    msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
        "🗑️ *Delete a task* — which one?",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(buttons),
    )
    ctx.user_data[_CHAT] = msg.chat_id  # type: ignore[index]
    ctx.user_data[_MSG]  = msg.message_id  # type: ignore[index]
    return DELETE_PICK


async def delete_pick_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    if query.data == "del_cancel":  # type: ignore[union-attr]
        await query.edit_message_text("❌ Cancelled.")  # type: ignore[union-attr]
        _schedule_end(ctx)
        return ConversationHandler.END

    task_id = int(query.data.split("_")[-1])  # type: ignore[union-attr]
    task = db.get_task(task_id)
    ctx.user_data["del_task_id"] = task_id  # type: ignore[index]

    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🗑️ Yes, delete", callback_data="del_yes"),
        InlineKeyboardButton("❌ Cancel",       callback_data="del_cancel"),
    ]])
    await query.edit_message_text(  # type: ignore[union-attr]
        f"Are you sure you want to delete *{task['name']}*?\n_This cannot be undone._",
        parse_mode="Markdown",
        reply_markup=keyboard,
    )
    return DELETE_CONFIRM


async def delete_confirm_cb(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    query = update.callback_query
    await query.answer()  # type: ignore[union-attr]
    if query.data == "del_yes":  # type: ignore[union-attr]
        task_id = ctx.user_data["del_task_id"]  # type: ignore[index]
        task = db.get_task(task_id)
        name = task["name"]
        db.delete_task(task_id)
        await query.edit_message_text(f"🗑️ *{name}* deleted.", parse_mode="Markdown")  # type: ignore[union-attr]
    else:
        await query.edit_message_text("❌ Cancelled.")  # type: ignore[union-attr]
    _schedule_end(ctx)
    return ConversationHandler.END


# ── Cancel fallback ────────────────────────────────────────────────────────────

async def cancel(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> int:
    await delete_message(update.message)  # type: ignore[arg-type]
    await _edit(ctx, "❌ Operation cancelled.")
    _schedule_end(ctx)
    return ConversationHandler.END


# ── ConversationHandlers ───────────────────────────────────────────────────────

add_conversation = ConversationHandler(
    entry_points=[CommandHandler("add", cmd_add)],
    states={
        ADD_NAME:     [MessageHandler(filters.TEXT & ~filters.COMMAND, add_got_name)],
        ADD_DURATION: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_got_duration)],
        ADD_CONFIRM:  [CallbackQueryHandler(add_confirm_cb, pattern="^add_")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
)

edit_conversation = ConversationHandler(
    entry_points=[CommandHandler("edit", cmd_edit)],
    states={
        EDIT_PICK:  [CallbackQueryHandler(edit_pick_cb,  pattern="^edit_")],
        EDIT_FIELD: [CallbackQueryHandler(edit_field_cb, pattern="^ef_")],
        EDIT_VALUE: [MessageHandler(filters.TEXT & ~filters.COMMAND, edit_value_msg)],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
)

delete_conversation = ConversationHandler(
    entry_points=[CommandHandler("delete", cmd_delete)],
    states={
        DELETE_PICK:    [CallbackQueryHandler(delete_pick_cb,    pattern="^del_")],
        DELETE_CONFIRM: [CallbackQueryHandler(delete_confirm_cb, pattern="^del_")],
    },
    fallbacks=[CommandHandler("cancel", cancel)],
    per_message=False,
)
