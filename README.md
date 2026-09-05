# DailyPilot

A personal Telegram-based daily planner, habit tracker, and reminder assistant.

## 1. Project Goal

DailyPilot is a personal Telegram bot designed to help manage daily activities, learning goals, habits, and reminders.

The initial goal is to make it easy to:

- Define daily tasks and habits.
- Assign a duration to each task.
- Receive a daily reminder at a scheduled time.
- Update the status of tasks throughout the day.
- Review what was completed at the end of the day.
- Add, edit, and remove habits/tasks at any time.
- Keep Telegram conversations clean by editing temporary interaction messages instead of creating unnecessary messages.

The system should be simple enough for everyday personal use while being designed so additional features can be added later.

---

## 2. Current Use Case

The initial use case is managing activities during vacation.

Example daily plan:

| Activity               |   Duration |
| ---------------------- | ---------: |
| Learn Python           |    2 hours |
| Study Machine Learning |     1 hour |
| Read                   | 30 minutes |
| Exercise               |     1 hour |

The user should be able to change this list whenever needed.

---

## 3. Core Features

### 3.1 Task / Habit Management

The user can:

- Add a new task/habit.
- Edit an existing task/habit.
- Delete a task/habit.
- View all active tasks/habits.
- Set the expected duration.
- Enable or disable tasks without permanently deleting them.

Example:

```text
Learn Python
Duration: 2 hours
Status: Active
```

Tasks should be flexible enough to support future scheduling options.

---

### 3.2 Daily Reminder

The bot sends a daily reminder at a configured time.

Default:

```text
09:00 AM every day
```

Example:

```text
Good morning!

Today's Plan

1. Learn Python — 2 hours
2. Study Machine Learning — 1 hour
3. Read — 30 minutes
4. Exercise — 1 hour
```

The reminder should be generated from the user's currently active tasks/habits.

---

### 3.3 Daily Task Status

The user can update the status of their tasks for the current day.

Possible statuses:

- Done
- Partially Done
- Skipped
- Not Started

Example:

```text
Learn Python
[Done] [Partial] [Skip]
```

The user should be able to update their status multiple times during the day.

---

### 3.4 End-of-Day Check-In

At a configurable time, the bot can remind the user to update their daily progress.

Example:

```text
Daily Check-In

You haven't finished updating today's tasks.

How did you do today?

[Update Tasks]
[View Today's Progress]
```

This notification should remain in the chat as a historical record.

---

## 4. Telegram Message Behavior

There are two different types of bot messages.

### 4.1 Temporary Interaction Messages

Messages used during commands and setup should be edited/reused whenever possible.

For example:

```text
/add
     ↓
Bot: Add a new task
     ↓
User: Learn Python
     ↓
Bot: How long?
     ↓
User: 2 hours
     ↓
Bot: Confirm?

[Confirm] [Cancel]
```

Instead of leaving every step in the chat, the bot should preferably maintain **one editable interaction message**.

This keeps the conversation clean.

---

### 4.2 Persistent Messages

Notifications and meaningful daily records should NOT be overwritten.

Examples:

- Daily 9 AM reminder.
- End-of-day check-in.
- Daily summary.
- Weekly summary (future feature).
- Important system notifications.

These messages should remain in the Telegram chat as history.

---

## 5. Basic Commands

Initial command ideas:

```text
/start
/help

/tasks
/add
/edit
/delete

/today
/update

/settings
```

The exact command structure can be changed during implementation if a better interaction design is found.

---

## 6. Example User Flow

### Morning

At 9:00 AM:

```text
DailyPilot

Good morning!

Today's Plan:

☐ Learn Python — 2h
☐ Machine Learning — 1h
☐ Read — 30m
☐ Exercise — 1h
```

### During the Day

User:

```text
/update
```

Bot provides an interactive task list:

```text
Today's Progress

Learn Python
[Done] [Partial] [Skip]

Machine Learning
[Done] [Partial] [Skip]

Exercise
[Done] [Partial] [Skip]
```

The bot edits the interaction message as the user makes selections.

### Evening

Bot sends:

```text
Daily Check-In

How did you do today?

Completed: 3/4

[Update Status]
[View Summary]
```

This message remains in the chat.

---

## 7. Data Requirements

The initial database should store at least:

### Tasks / Habits

```text
id
name
description
duration
active
created_at
updated_at
```

### Daily Task Records

Daily history should be stored separately from the task definition.

```text
id
task_id
date
status
actual_duration
created_at
updated_at
```

This separation is important.

For example, if:

```text
Learn Python
```

exists for three months, the bot should still be able to maintain:

```text
September 1 → Done
September 2 → Partial
September 3 → Skipped
September 4 → Done
...
```

Changing the task itself should not destroy historical records.

---

## 8. Scheduling

The bot needs a persistent scheduler capable of running even when the user has not interacted with the bot.

Initial scheduled jobs:

```text
09:00 → Daily plan reminder

Evening → Daily check-in
```

The scheduling system should eventually support:

- Daily schedules.
- Custom reminder times.
- One-time reminders.
- Recurring reminders.
- Different schedules for different tasks.

---

## 9. Initial Architecture

Initial architecture:

```text
Telegram
    │
    ▼
Telegram Bot
    │
    ├── Task / Habit Manager
    │
    ├── Daily Progress Manager
    │
    ├── Reminder Scheduler
    │
    └── Settings
          │
          ▼
       Database
```

Initial deployment target:

```text
Oracle Cloud Free Tier
        │
        ▼
Ubuntu VM
        │
        ▼
DailyPilot
        │
        ├── Telegram Bot
        ├── Scheduler
        └── Database
```

The bot should run continuously so scheduled notifications can be delivered reliably.

---

## 10. Initial Technology Direction

Possible initial stack:

- **Language:** Python
- **Telegram:** Python Telegram Bot framework
- **Database:** SQLite
- **Scheduler:** Python-based scheduler / background job system
- **Server:** Ubuntu
- **Hosting:** Oracle Cloud Free Tier

The stack can be changed later if there is a strong reason.

---

# MVP Scope

The first version should only focus on:

- [ ] Telegram bot setup
- [ ] `/start`
- [ ] Add task/habit
- [ ] Edit task/habit
- [ ] Delete task/habit
- [ ] List active tasks
- [ ] Duration for each task
- [ ] Daily 9 AM reminder
- [ ] Daily task status
- [ ] End-of-day check-in
- [ ] Persistent daily history
- [ ] Temporary interactive messages
- [ ] SQLite database
- [ ] Background scheduler
- [ ] Deploy to Oracle Cloud
- [ ] Run continuously

---

# Future Features

Features that can be added after the MVP:

### Planning

- Custom schedules.
- Different tasks on different days.
- Time-specific tasks.
- One-time tasks.
- Recurring tasks.

### Habit Tracking

- Habit streaks.
- Completion percentage.
- Weekly/monthly statistics.
- Long-term progress.
- Habit history.

### Reminders

- Custom reminder times.
- Multiple reminders per day.
- Snooze.
- One-time reminders.
- Smart reminders.

### Reports

- Daily summary.
- Weekly summary.
- Monthly summary.
- Productivity statistics.
- Time spent per activity.

### AI

Eventually, DailyPilot could support natural-language commands such as:

> "Tomorrow I want to study AI for 2 hours and work out for an hour."

The AI could convert this into structured tasks automatically.

Other possible AI features:

- Automatically plan a day.
- Suggest realistic schedules.
- Reschedule unfinished tasks.
- Summarize weekly productivity.
- Answer questions about personal activity history.

---

# Design Principles

1. **Keep the Telegram chat clean.**
   Temporary interactions should reuse/edit messages whenever possible.

2. **Never lose historical data.**
   Daily progress should be stored separately from the current task configuration.

3. **Keep the MVP simple.**
   Do not introduce AI or complicated scheduling until the basic system works reliably.

4. **Design for expansion.**
   The database and architecture should allow future features without requiring a complete rewrite.

5. **Reliable scheduled notifications.**
   The bot should continue running independently of user interaction.

6. **Personal-first.**
   The system is initially designed for one personal user rather than a large public audience.

---

# Development Roadmap

## Phase 1 — Foundation

- Telegram bot
- Project structure
- Configuration/environment variables
- SQLite database
- Basic `/start` and `/help`

## Phase 2 — Task Management

- Add
- Edit
- Delete
- List
- Activate/deactivate
- Duration

## Phase 3 — Daily Tracking

- Generate today's tasks
- Task status
- Daily history
- Update interactions

## Phase 4 — Notifications

- 9 AM daily reminder
- End-of-day check-in
- Persistent notification messages
- Background scheduler

## Phase 5 — Deployment

- Oracle Cloud VM
- Ubuntu setup
- Process management
- Automatic restart
- Logging
- Backup strategy

## Phase 6 — Expansion

- Custom schedules
- Streaks
- Statistics
- Reports
- Advanced reminders
- AI assistant
- Natural-language task creation

---

# Current Goal

Build a reliable personal Telegram assistant that answers one simple question every day:

> **"What should I do today, and how did I actually do?"**

Start small, make it reliable, then gradually turn it into a personal productivity system.
