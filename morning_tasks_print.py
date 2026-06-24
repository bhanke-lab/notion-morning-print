#!/usr/bin/env python3
"""morning_tasks_print.py - print today's Notion task checklist to your printer."""
import os, sys, time, argparse, threading, itertools, subprocess, tempfile
from contextlib import contextmanager
from datetime import date, timedelta
from dotenv import load_dotenv
from notion_client import Client

try:
    sys.stdout.reconfigure(encoding="utf-8")  # so the spinner + check marks render
except Exception:
    pass

load_dotenv()

NOTION_TOKEN = os.environ["NOTION_TOKEN"]
DATABASE_ID  = os.environ["NOTION_DATABASE_ID"]
PRINTER_NAME = os.environ.get("PRINTER_NAME")
LIST_TITLE   = os.environ.get("LIST_TITLE", "TODAY'S TASKS")

# ---------- adapt to your database's schema via .env ----------
PROP_TITLE    = os.environ.get("PROP_TITLE", "Task name")
PROP_DATE     = os.environ.get("PROP_DATE", "Schedule")
PROP_STATUS   = os.environ.get("PROP_STATUS", "Status")
PROP_PRIORITY = os.environ.get("PROP_PRIORITY", "Priority")
PROP_PARENT   = os.environ.get("PROP_PARENT", "Parent task")

DONE = {s.strip() for s in os.environ.get("DONE_STATUSES", "Done,Ordered,Received,RFQ Out").split(",")}
PRIORITY_LIST = [s.strip() for s in os.environ.get("PRIORITY_ORDER", "URGENT,1,2,3,4,Storage,Recurring").split(",")]
PRIORITY_ORDER = {name: i for i, name in enumerate(PRIORITY_LIST)}
IN_PROGRESS = os.environ.get("IN_PROGRESS_STATUS", "In progress")
URGENT      = os.environ.get("URGENT_PRIORITY", "URGENT")

TARGET, CAP, FILL_DAYS = 8, 14, 3

VERBOSE = False
notion = Client(auth=NOTION_TOKEN)
parent_cache = {}
TODAY = date.today().isoformat()

# ---------- live-run visual ----------
class Spinner:
    FRAMES = "⠋⠙⠹⠸⠼⠴⠦⠧⠇⠏"
    def __init__(self, label):
        self.label, self._stop = label, threading.Event()
        self._t = threading.Thread(target=self._spin, daemon=True)
    def _spin(self):
        for ch in itertools.cycle(self.FRAMES):
            if self._stop.is_set(): break
            sys.stdout.write(f"\r  {ch} {self.label} "); sys.stdout.flush()
            time.sleep(0.08)
    def __enter__(self): self._t.start(); return self
    def __exit__(self, exc_type, *a):
        self._stop.set(); self._t.join()
        mark = "\033[32m✓\033[0m" if exc_type is None else "\033[31m✗\033[0m"
        sys.stdout.write(f"\r  {mark} {self.label}      \n"); sys.stdout.flush()

@contextmanager
def step(label):
    if not VERBOSE:
        yield; return
    with Spinner(label):
        yield

def say(msg=""):
    if VERBOSE: print(msg)

# ---------- defensive property helpers ----------
def title(p, name=None):
    pr = p["properties"].get(name or PROP_TITLE, {})
    return "".join(t["plain_text"] for t in pr.get("title", [])).strip()
def select(p, name):
    pr = p["properties"].get(name) or {}
    v = pr.get("select");  return v["name"] if v else None
def status(p):
    pr = p["properties"].get(PROP_STATUS) or {}
    v = pr.get("status");  return v["name"] if v else None
def due(p):
    v = p["properties"]["Schedule"].get("date")
    if not v:
        return None
    return (v.get("end") or v["start"])[:10]
def parent_title(p):
    pr = p["properties"].get(PROP_PARENT) or {}
    rel = pr.get("relation") or []
    if not rel: return None
    pid = rel[0]["id"]
    if pid not in parent_cache:
        parent_cache[pid] = title(notion.pages.retrieve(pid))
    return parent_cache[pid]

# ---------- data ----------
def query_all(filt):
    out, cursor = [], None
    while True:
        kw = {"database_id": DATABASE_ID, "filter": filt}
        if cursor: kw["start_cursor"] = cursor
        r = notion.databases.query(**kw)
        out += r["results"]
        if not r.get("has_more"): break
        cursor = r["next_cursor"]
    return out

def gather():
    horizon = (date.today() + timedelta(days=FILL_DAYS)).isoformat()
    filters = [
        {"property": PROP_DATE,     "date":   {"on_or_before": horizon}},
        {"property": PROP_STATUS,   "status": {"equals": IN_PROGRESS}},
        {"property": PROP_PRIORITY, "select": {"equals": URGENT}},
    ]
    pages = {}
    for f in filters:
        for p in query_all(f):
            pages[p["id"]] = p
    return [p for p in pages.values() if status(p) not in DONE]

def rank(p):
    return (PRIORITY_ORDER.get(select(p, PROP_PRIORITY) or "", 9), due(p) or "9999")

def choose(pages):
    must, optional = [], []
    for p in pages:
        d = due(p)
        if (d and d <= TODAY) or select(p, PROP_PRIORITY) == URGENT:
            must.append(p)
        else:
            optional.append(p)
    must.sort(key=rank); optional.sort(key=rank)
    chosen = must[:]
    for p in optional:
        if len(chosen) >= TARGET: break
        chosen.append(p)
    return chosen[:CAP]

def grouped(chosen):
    overdue = sorted([p for p in chosen if due(p) and due(p) <  TODAY], key=rank)
    today   = sorted([p for p in chosen if due(p) and due(p) == TODAY], key=rank)
    ahead   = sorted([p for p in chosen if p not in overdue and p not in today], key=rank)
    return (("OVERDUE", overdue), ("TODAY", today), ("PICKED AHEAD", ahead))

# ---------- output ----------
def render(chosen):
    def line(p):
        s = f"[ ] (P{select(p, PROP_PRIORITY) or '-'}) {title(p)}"
        par = parent_title(p)
        if par: s += f"\n        parent: {par}"
        if due(p): s += f"\n        due {due(p)}"
        return s
    out = [f"{LIST_TITLE} - {date.today():%a %b %d, %Y}", "=" * 42, ""]
    has_tasks = False
    for hdr, group in grouped(chosen):
        if not group: continue
        has_tasks = True
        out.append(hdr); out.append("-" * len(hdr))
        out += [line(p) for p in group]
        out.append("")
    if not has_tasks:
        out.append("Nothing pressing. Go find something to fix.")
        out.append("")
    out.append("-" * 42)
    out.append("[ ] End of day: mark completed tasks done in Notion")
    return "\n".join(out)

def show_chosen(chosen):
    say(f"\n  Tasks chosen ({len(chosen)}):")
    for hdr, group in grouped(chosen):
        if not group: continue
        say(f"    {hdr}")
        for p in group:
            tail = f"  [due {due(p)}]" if due(p) else ""
            par = parent_title(p)
            par = f"  (parent: {par})" if par else ""
            say(f"      • P{select(p, PROP_PRIORITY) or '-'}  {title(p)}{tail}{par}")
    say()

def send(text):
    path = os.path.join(tempfile.gettempdir(), "morning_tasks.txt")
    with open(path, "w", encoding="utf-8") as f:
        f.write(text)
    target = f'-Name "{PRINTER_NAME}"' if PRINTER_NAME else ""
    ps = f'Get-Content -Raw -Encoding UTF8 "{path}" | Out-Printer {target}'
    subprocess.run(["powershell", "-NoProfile", "-Command", ps], check=True)

# ---------- main ----------
def main():
    global VERBOSE
    ap = argparse.ArgumentParser(description="Print today's Notion task checklist.")
    ap.add_argument("-q", "--quiet", action="store_true", help="suppress live progress (for scheduled runs)")
    ap.add_argument("--dry-run", action="store_true", help="build the list but do not print")
    args = ap.parse_args()
    VERBOSE = not args.quiet

    say(f"\n  {LIST_TITLE} - {date.today():%a %b %d, %Y}\n")

    with step("Fetching tasks from Notion"):
        pages = gather()
    say(f"    pulled {len(pages)} candidate task(s)")

    with step("Choosing today's tasks"):
        chosen = choose(pages)
    show_chosen(chosen)

    if args.dry_run:
        say("  Dry run, skipping print.")
        if not VERBOSE: print(render(chosen))
        return

    with step(f"Connecting to printer ({PRINTER_NAME or 'default'})"):
        time.sleep(0.4)
    with step(f"Printing {len(chosen)} task(s)"):
        send(render(chosen))

    say("\n  Done.\n")

if __name__ == "__main__":
    main()