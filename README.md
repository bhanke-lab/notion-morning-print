# notion-morning-print

Prints a prioritized checklist of your day's tasks from a Notion database to
your printer every morning. Applies rule-based "discretion" (overdue + due
today + urgent + in-progress, then fills to a full day), groups by Overdue /
Today / Picked Ahead, and prints via PowerShell Out-Printer on Windows.

Works with any Notion database that has a date, status, and (optional)
priority property. Map your column and option names in `.env`. This also allows for further customization of your database as needed, do whatcha want.

## Requirements

- Windows PC, on (not asleep) at run time
- Python 3.10+
- A Notion internal integration with access to your tasks database

## Setup

1. git clone <bhanke-lab/notion-morning-print> C:\Scripts\notion-morning-print
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

## Scheduling (Windows)

Can use Task Scheduler, or use the below built in pwsh script to make it easier. This prevents pw protection issues.

From the repo folder, with the venv created:

    .\setup_schedule.ps1

This registers a Task Scheduler job using an Interactive logon type, so it
needs no stored password and runs while you are logged on (a locked screen
counts). If PowerShell blocks the script, allow it for your user once:

    Set-ExecutionPolicy -Scope CurrentUser RemoteSigned

### Adjusting the time or days

Re-run the script with new values. The -Force flag updates the existing task:

    .\setup_schedule.ps1 -Time "6:30AM"
    .\setup_schedule.ps1 -Days Monday,Wednesday,Friday -Time "5:00AM"
    .\setup_schedule.ps1 -Days Saturday,Sunday -Time "7:00AM"

Time accepts formats like "5:15AM", "06:30", "17:00". Days are full English
weekday names, comma-separated.

Or change it in the GUI: Task Scheduler > Notion Morning Print >
Triggers tab > Edit > set the new time > OK.

### Removing it

    Unregister-ScheduledTask -TaskName "Notion Morning Print" -Confirm:$false

## Tuning

- TARGET / CAP / FILL_DAYS constants control list length and look-ahead

## Notes

- Designed for Notion API version 2022-06-28 (notion-client 2.2.1, pinned)
- Linux/Mac: replace the `send()` PowerShell call with `lp`, adjust the scheduling workflow per Linux/Mac documentation, or reach out and i'll probably just build it.
