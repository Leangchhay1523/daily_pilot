"""
handlers/stats.py — /stats command.

Shows personal analytics for the last 30 days:
  - Overall completion rate
  - Per-task rates (most/least consistent)
  - Best day of the week
  - Current streaks

Temporary message, auto-deleted after 50 s.
"""

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from app import database as db
from app.helpers import delete_later, delete_message


def _pct_bar(rate: float, width: int = 10) -> str:
    filled = round(rate * width)
    return "█" * filled + "░" * (width - filled)


def _build_stats_text() -> str:
    data = db.get_stats(days=30)

    if data["total_records"] == 0:
        return (
            "📈 *Your Stats*\n\n"
            "Not enough data yet — keep tracking for a few days!"
        )

    overall = data["overall_rate"]
    bar     = _pct_bar(overall)
    lines   = [
        f"📈 *Your Stats* (last {data['days']} days)\n",
        f"`{bar}` {int(overall * 100)}% overall",
        f"Completed: *{data['total_completed']} / {data['total_records']}* task-days\n",
    ]

    # Per-task breakdown
    if data["task_stats"]:
        lines.append("📋 *Per Task*")
        sorted_tasks = sorted(data["task_stats"], key=lambda t: t["rate"], reverse=True)
        for t in sorted_tasks:
            b   = _pct_bar(t["rate"], width=8)
            pct = int(t["rate"] * 100)
            lines.append(f"  `{b}` {pct:3d}%  {t['name']}")
        lines.append("")

    # Highlights
    if data["best_task"]:
        lines.append(f"🏆 Most consistent: *{data['best_task']['name']}* ({int(data['best_task']['rate']*100)}%)")
    if data["worst_task"] and data["worst_task"] != data["best_task"]:
        lines.append(f"⚠️ Needs attention: *{data['worst_task']['name']}* ({int(data['worst_task']['rate']*100)}%)")
    if data["best_day"]:
        lines.append(f"📅 Best day: *{data['best_day']}*")

    # Active streaks
    streaks = db.get_all_streaks()
    active  = [(t["name"], streaks.get(t["id"], 0))
               for t in db.get_active_tasks()
               if streaks.get(t["id"], 0) >= 2]
    if active:
        lines.append("\n🔥 *Current Streaks*")
        for name, s in sorted(active, key=lambda x: -x[1]):
            lines.append(f"   {name}: *{s} days*")

    return "\n".join(lines)


async def cmd_stats(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await delete_message(update.message)  # type: ignore[arg-type]
    text = _build_stats_text()
    msg  = await update.effective_chat.send_message(  # type: ignore[union-attr]
        text, parse_mode="Markdown"
    )
    delete_later(ctx, msg.chat_id, msg.message_id, delay=50)


stats_handler = CommandHandler("stats", cmd_stats)
