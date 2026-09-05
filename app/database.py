"""
database.py — SQLite persistence layer for DailyPilot.

Tables
------
tasks          — habit/task definitions (static).
daily_records  — per-day completion records (history).
notes          — daily journal entries.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path
from typing import Optional

DB_PATH = Path(__file__).parent.parent / "data" / "daily_pilot.db"

COMPLETED = ("done", "partial")
DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
DAY_NAMES_FULL = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def init_db() -> None:
    """Create tables if they don't exist."""
    with _connect() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS tasks (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                name        TEXT    NOT NULL,
                description TEXT    DEFAULT '',
                duration    TEXT    NOT NULL,
                active      INTEGER NOT NULL DEFAULT 1,
                created_at  TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at  TEXT    NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS daily_records (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id         INTEGER NOT NULL REFERENCES tasks(id) ON DELETE CASCADE,
                date            TEXT    NOT NULL,
                status          TEXT    NOT NULL DEFAULT 'not_started',
                actual_duration TEXT    DEFAULT NULL,
                created_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at      TEXT    NOT NULL DEFAULT (datetime('now')),
                UNIQUE(task_id, date)
            );

            CREATE TABLE IF NOT EXISTS notes (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                date       TEXT    NOT NULL UNIQUE,
                text       TEXT    NOT NULL,
                created_at TEXT    NOT NULL DEFAULT (datetime('now')),
                updated_at TEXT    NOT NULL DEFAULT (datetime('now'))
            );
            """
        )


# ── Task helpers ───────────────────────────────────────────────────────────────

def add_task(name: str, duration: str, description: str = "") -> int:
    with _connect() as conn:
        cur = conn.execute(
            "INSERT INTO tasks (name, description, duration) VALUES (?, ?, ?)",
            (name, description, duration),
        )
        return cur.lastrowid  # type: ignore[return-value]


def get_all_tasks() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute("SELECT * FROM tasks ORDER BY id").fetchall()


def get_active_tasks() -> list[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE active = 1 ORDER BY id"
        ).fetchall()


def get_task(task_id: int) -> Optional[sqlite3.Row]:
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()


def update_task(
    task_id: int,
    name: Optional[str] = None,
    duration: Optional[str] = None,
    description: Optional[str] = None,
    active: Optional[bool] = None,
) -> None:
    fields, values = [], []
    if name is not None:
        fields.append("name = ?"); values.append(name)
    if duration is not None:
        fields.append("duration = ?"); values.append(duration)
    if description is not None:
        fields.append("description = ?"); values.append(description)
    if active is not None:
        fields.append("active = ?"); values.append(int(active))
    if not fields:
        return
    fields.append("updated_at = datetime('now')")
    values.append(task_id)
    with _connect() as conn:
        conn.execute(
            f"UPDATE tasks SET {', '.join(fields)} WHERE id = ?",
            values,
        )


def delete_task(task_id: int) -> None:
    with _connect() as conn:
        conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))


# ── Daily record helpers ───────────────────────────────────────────────────────

def ensure_daily_records(day: Optional[date] = None) -> None:
    """Create 'not_started' records for every active task that has none today."""
    today = (day or date.today()).isoformat()
    with _connect() as conn:
        active = conn.execute("SELECT id FROM tasks WHERE active = 1").fetchall()
        for row in active:
            conn.execute(
                "INSERT OR IGNORE INTO daily_records (task_id, date, status) VALUES (?, ?, 'not_started')",
                (row["id"], today),
            )


def get_daily_records(day: Optional[date] = None) -> list[sqlite3.Row]:
    today = (day or date.today()).isoformat()
    with _connect() as conn:
        return conn.execute(
            """
            SELECT dr.*, t.name, t.duration
            FROM daily_records dr
            JOIN tasks t ON dr.task_id = t.id
            WHERE dr.date = ?
            ORDER BY t.id
            """,
            (today,),
        ).fetchall()


def set_record_status(record_id: int, status: str) -> None:
    with _connect() as conn:
        conn.execute(
            "UPDATE daily_records SET status = ?, updated_at = datetime('now') WHERE id = ?",
            (status, record_id),
        )


def daily_summary(day: Optional[date] = None) -> dict:
    """Return a summary dict for the given day."""
    records = get_daily_records(day)
    total       = len(records)
    done        = sum(1 for r in records if r["status"] == "done")
    partial     = sum(1 for r in records if r["status"] == "partial")
    skipped     = sum(1 for r in records if r["status"] == "skipped")
    not_started = sum(1 for r in records if r["status"] == "not_started")
    score       = done + partial * 0.5
    return {
        "total": total,
        "done": done,
        "partial": partial,
        "skipped": skipped,
        "not_started": not_started,
        "score": score,
        "records": records,
    }


# ── Streak helpers ─────────────────────────────────────────────────────────────

def get_streak(task_id: int) -> int:
    """Consecutive days ending today (or yesterday) with done/partial status."""
    today = date.today()
    streak = 0
    check = today
    with _connect() as conn:
        # If today has no record or not_started, start from yesterday
        row = conn.execute(
            "SELECT status FROM daily_records WHERE task_id=? AND date=?",
            (task_id, today.isoformat()),
        ).fetchone()
        if not row or row["status"] not in COMPLETED:
            check = today - timedelta(days=1)

        while True:
            row = conn.execute(
                "SELECT status FROM daily_records WHERE task_id=? AND date=?",
                (task_id, check.isoformat()),
            ).fetchone()
            if row and row["status"] in COMPLETED:
                streak += 1
                check -= timedelta(days=1)
            else:
                break
    return streak


def get_all_streaks() -> dict[int, int]:
    """Return {task_id: streak} for every active task."""
    tasks = get_active_tasks()
    return {t["id"]: get_streak(t["id"]) for t in tasks}


# ── Weekly grid helpers ────────────────────────────────────────────────────────

def get_week_data(ref_day: Optional[date] = None) -> tuple[list, list[date]]:
    """
    Returns (task_rows, dates) where:
      task_rows = [{"name": str, "duration": str, "statuses": [status, ...7]}]
      dates     = list of 7 date objects (oldest → today)
    """
    today = ref_day or date.today()
    dates = [today - timedelta(days=i) for i in range(6, -1, -1)]  # oldest first

    with _connect() as conn:
        tasks = conn.execute(
            "SELECT * FROM tasks WHERE active = 1 ORDER BY id"
        ).fetchall()
        rows = []
        for t in tasks:
            statuses = []
            for d in dates:
                row = conn.execute(
                    "SELECT status FROM daily_records WHERE task_id=? AND date=?",
                    (t["id"], d.isoformat()),
                ).fetchone()
                statuses.append(row["status"] if row else "none")
            rows.append({
                "id": t["id"],
                "name": t["name"],
                "duration": t["duration"],
                "statuses": statuses,
            })
    return rows, dates


# ── Notes helpers ──────────────────────────────────────────────────────────────

def save_note(text: str, day: Optional[date] = None) -> None:
    today = (day or date.today()).isoformat()
    with _connect() as conn:
        conn.execute(
            """
            INSERT INTO notes (date, text)
            VALUES (?, ?)
            ON CONFLICT(date) DO UPDATE SET text=excluded.text, updated_at=datetime('now')
            """,
            (today, text),
        )


def get_note(day: Optional[date] = None) -> Optional[sqlite3.Row]:
    today = (day or date.today()).isoformat()
    with _connect() as conn:
        return conn.execute(
            "SELECT * FROM notes WHERE date=?", (today,)
        ).fetchone()


# ── Stats helpers ──────────────────────────────────────────────────────────────

def get_stats(days: int = 30) -> dict:
    """Aggregate analytics for the last `days` days."""
    today      = date.today()
    start_date = today - timedelta(days=days - 1)

    with _connect() as conn:
        records = conn.execute(
            """
            SELECT dr.task_id, dr.date, dr.status, t.name
            FROM daily_records dr
            JOIN tasks t ON dr.task_id = t.id
            WHERE dr.date >= ? AND dr.date <= ?
            ORDER BY dr.date
            """,
            (start_date.isoformat(), today.isoformat()),
        ).fetchall()

    # Per-task stats
    task_map: dict[int, dict] = {}
    # Per-weekday stats {0=Mon..6=Sun: {total, completed}}
    dow_map: dict[int, dict] = {i: {"total": 0, "done": 0} for i in range(7)}

    for r in records:
        tid = r["task_id"]
        if tid not in task_map:
            task_map[tid] = {"name": r["name"], "total": 0, "done": 0}
        task_map[tid]["total"] += 1
        completed = r["status"] in COMPLETED
        if completed:
            task_map[tid]["done"] += 1

        d   = date.fromisoformat(r["date"])
        dow = d.weekday()
        dow_map[dow]["total"] += 1
        if completed:
            dow_map[dow]["done"] += 1

    # Compute rates
    for v in task_map.values():
        v["rate"] = v["done"] / v["total"] if v["total"] else 0.0

    # Best / worst task
    def _rate(item):
        return item[1]["rate"]

    best_task  = max(task_map.items(), key=_rate)[1] if task_map else None
    worst_task = min(task_map.items(), key=_rate)[1] if task_map else None

    # Best day of week
    active_days = {k: v for k, v in dow_map.items() if v["total"] > 0}
    if active_days:
        best_dow = max(active_days, key=lambda k: active_days[k]["done"] / active_days[k]["total"])
    else:
        best_dow = None

    total_records   = len(records)
    total_completed = sum(1 for r in records if r["status"] in COMPLETED)

    return {
        "days": days,
        "total_records": total_records,
        "total_completed": total_completed,
        "overall_rate": total_completed / total_records if total_records else 0.0,
        "task_stats": list(task_map.values()),
        "best_task": best_task,
        "worst_task": worst_task,
        "best_day": DAY_NAMES_FULL[best_dow] if best_dow is not None else None,
    }
