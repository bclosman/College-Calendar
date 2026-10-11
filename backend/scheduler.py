import json
from canvasapi import exceptions
from datetime import datetime
import time
from apscheduler.schedulers.blocking import BlockingScheduler
from pathlib import Path
from .database import init_db, print_events
from .services.ical_sync import sync_assignments_from_ical, sync_calendar
from .services.canvas_sync import sync_assignments_from_canvas

CALENDAR_PATH = Path(__file__).resolve().parent.parent / "calendars.json"

def get_calendars():
    with open(CALENDAR_PATH, "r", encoding="utf-8") as file:
        calendars = json.load(file)
    
    return calendars

def get_calendar_url(name: str) -> str:
    calendars = get_calendars()
    for calendar in calendars["calendars"]:
        if calendar["name"] == name:
            return calendar["url"]

    raise ValueError(f"Calendar '{name}' not found")

def sync_assignments():
    start_time = time.perf_counter()
    print("Starting Canvas assignment sync...")

    try:
        sync_assignments_from_canvas()
    except exceptions.InvalidAccessToken or exceptions.ResourceDoesNotExist:
        print("Canvas API Failed! Using iCal...")
        canvas_url = get_calendar_url("Canvas")
        sync_assignments_from_ical(canvas_url)

    duration = time.perf_counter() - start_time
    print(f"Canvas assignment took {duration:.6f} seconds to sync!")

def sync_events():
    calendars = get_calendars()
    for calendar in calendars["calendars"]:
        start_time = time.perf_counter()
        print(f"Starting {calendar["name"]} Calendar sync...")

        sync_calendar(calendar["url"], calendar["name"])
        
        duration = time.perf_counter() - start_time
        print(f"{calendar["name"]} Calendar took {duration:.6f} seconds to sync!")

def run_scheduler():
    init_db()

    scheduler = BlockingScheduler()

    scheduler.add_job(
        sync_assignments,
        "interval",
        minutes=5,
        next_run_time=datetime.now(),
        id="assignments",
        max_instances=1,
        coalesce=True
    )

    scheduler.add_job(
        sync_events,
        "interval",
        minutes=5,
        next_run_time=datetime.now(),
        id="events",
        max_instances=1,
        coalesce=True
    )

    scheduler.start()

if __name__ == "__main__":
    run_scheduler()