"""
handlers/summary.py — /summary command.

Shows today's task results with per-task status, a score, and streak info.
This is a temporary message (auto-deleted after 40 s).
"""

from datetime import date

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from app import database as db
from app.helpers import delete_later, delete_message

STATUS_EMOJI = {
    "done":        "✅",
    "partial":     "🔶",
    "skipped":     "⏭️",
    "not_started": "☐",
}

STATUS_LABEL = {
    "done":        "Done",
    "partial":     "Partial",
    "skipped":     "Skipped",
    "not_started": "Not started",
}


def _build_summary(day: date | None = None) -> str:
    today    = day or date.today()
    summary  = db.daily_summary(today)
    records  = summary["records"]
    streaks  = db.get_all_streaks()
    note     = db.get_note(today)

    if not records:
        return (
            f"📊 *Daily Summary — {today.strftime('%b %-d')}*\n\n"
            "No tasks were tracked today."
        )

    lines = [f"📊 *Daily Summary — {today.strftime('%b %-d')}*\n"]

    for r in records:
        emoji = STATUS_EMOJI.get(r["status"], "☐")
        label = STATUS_LABEL.get(r["status"], "")
        streak = streaks.get(r["task_id"], 0)
        streak_txt = f"  🔥 {streak}" if streak >= 2 else ""
        lines.append(f"{emoji} *{r['name']}* — {r['duration']}{streak_txt}")
        lines.append(f"    └ {label}")

    # Score
    total = summary["total"]
    score = summary["score"]
    pct   = int((score / total) * 100) if total else 0
    bar_filled = int(pct / 10)
    bar = "█" * bar_filled + "░" * (10 - bar_filled)
    lines.append(f"\n`{bar}` {pct}%")
    lines.append(f"Score: *{score:.1f} / {total}* tasks")

    # Streaks summary
    active_streaks = [(r["name"], streaks.get(r["task_id"], 0))
                      for r in records if streaks.get(r["task_id"], 0) >= 2]
    if active_streaks:
        lines.append("\n🔥 *Active Streaks*")
        for name, s in active_streaks:
            lines.append(f"   {name} — {s} days")

    # Journal note
    if note:
        lines.append(f"\n📓 *Note:* _{note['text']}_")

    return "\n".join(lines)


async def cmd_summary(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await delete_message(update.message)  # type: ignore[arg-type]
    text = _build_summary()
    msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
        text, parse_mode="Markdown"
    )
    delete_later(ctx, msg.chat_id, msg.message_id, delay=40)


summary_handler = CommandHandler("summary", cmd_summary)
