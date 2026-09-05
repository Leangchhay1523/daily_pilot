"""
handlers/weekly.py — /week command.

Shows a 7-day completion grid for all active tasks.
Temporary message — auto-deleted after 50 s.
"""

from datetime import date

from telegram import Update
from telegram.ext import CommandHandler, ContextTypes

from app import database as db
from app.helpers import delete_later, delete_message

# Single-char symbols used in monospace grid
SYMBOL = {
    "done":        "✓",
    "partial":     "~",
    "skipped":     "x",
    "not_started": "·",
    "none":        " ",
}

DAY_SHORT = ["Mo", "Tu", "We", "Th", "Fr", "Sa", "Su"]


def _build_week_text() -> str:
    rows, dates = db.get_week_data()

    if not rows:
        return (
            "📅 *Weekly Progress*\n\n"
            "No active tasks. Use /add to create some."
        )

    # Header row: day abbreviations aligned
    today = date.today()
    header_labels = []
    for d in dates:
        label = DAY_SHORT[d.weekday()]
        if d == today:
            label = f"*{label}*"  # bold today — note: won't render in code block
        header_labels.append(label)

    # Max name length (capped at 14 chars)
    max_name = min(14, max(len(r["name"]) for r in rows))

    header = " " * (max_name + 1) + "  ".join(DAY_SHORT[d.weekday()] for d in dates)

    lines = [
        "📅 *Weekly Progress*\n",
        f"```",
        header,
        "─" * len(header),
    ]

    for r in rows:
        name_trunc = r["name"][:max_name].ljust(max_name)
        symbols    = "  ".join(SYMBOL.get(s, " ") for s in r["statuses"])
        lines.append(f"{name_trunc} {symbols}")

    lines.append("─" * len(header))
    lines.append("✓ Done  ~ Partial  x Skip  · None")
    lines.append("```")

    # Per-task completion rate for the week
    lines.append("\n📈 *This Week*")
    for r in rows:
        done_count = sum(1 for s in r["statuses"] if s in ("done", "partial"))
        total = sum(1 for s in r["statuses"] if s != "none")
        if total:
            pct = int(done_count / total * 100)
            streak = db.get_streak(r["id"])
            streak_txt = f"  🔥{streak}" if streak >= 2 else ""
            lines.append(f"  {r['name'][:20]}: {done_count}/{total} ({pct}%){streak_txt}")

    return "\n".join(lines)


async def cmd_week(update: Update, ctx: ContextTypes.DEFAULT_TYPE) -> None:
    await delete_message(update.message)  # type: ignore[arg-type]
    text = _build_week_text()
    msg = await update.effective_chat.send_message(  # type: ignore[union-attr]
        text, parse_mode="Markdown"
    )
    delete_later(ctx, msg.chat_id, msg.message_id, delay=50)


week_handler = CommandHandler("week", cmd_week)
