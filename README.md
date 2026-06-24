# notion-morning-print

Prints a prioritized checklist of your day's tasks from a Notion database to
your printer every morning. Applies rule-based "discretion" (overdue + due
today + urgent + in-progress, then fills to a full day), groups by Overdue /
Today / Picked Ahead, and prints via PowerShell Out-Printer on Windows.

Works with any Notion database that has a date, status, and (optional)
priority property. Map your column and option names in `.env`.

## Requirements

- Windows PC, on (not asleep) at run time
- Python 3.10+
- A Notion internal integration with access to your tasks database

## Setup

1. git clone <repo> C:\Scripts\notion-morning-print
2. python -m venv .venv && .\.venv\Scripts\Activate.ps1
3. pip install -r requirements.txt
4. cp .env.example .env  and fill it in:
   - NOTION_TOKEN from notion.so/my-integrations
   - NOTION_DATABASE_ID = 32-char ID in your database URL
   - PROP_*and*_STATUS / PRIORITY values to match your schema
   - PRINTER_NAME = exact Windows printer name, or blank for default
5. Share the database with the integration (••• > Connections)
6. Test: python morning_tasks_print.py --dry-run

## Usage

- python morning_tasks_print.py            # live view, then prints
- python morning_tasks_print.py --dry-run  # live view, no paper
- python morning_tasks_print.py --quiet    # silent, for Task Scheduler

## Scheduling (Task Scheduler)

- Trigger: Daily, weekdays, 5:15 AM
- Action: <repo>\.venv\Scripts\pythonw.exe  with argument  morning_tasks_print.py --quiet
- Start in: the repo folder (so it finds .env)
- Check "Run whether user is logged on or not" and
  "Run task as soon as possible after a missed start"

## Tuning

- TARGET / CAP / FILL_DAYS constants control list length and look-ahead

## Notes

- Designed for Notion API version 2022-06-28 (notion-client 2.2.1, pinned)
- Linux/Mac: replace the `send()` PowerShell call with `lp`
