import json
import os
import time as time_module
from canvasapi import exceptions
from datetime import date, datetime, time, timedelta, timezone
from dotenv import load_dotenv
from apscheduler.schedulers.blocking import BlockingScheduler
from pathlib import Path
from zoneinfo import ZoneInfo

from .database import init_db, get_assignments, remove_assignments, remove_events
from .services.ical_sync import sync_assignments_from_ical, sync_calendar
from .services.canvas_sync import sync_assignments_from_canvas
from .services.logger import Logger
from .services.notification import send_notification
from .workers.notification_worker import NotificationWorker

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
    start_time = time_module.perf_counter()
    print("Starting Canvas assignment sync...")

    try:
        sync_assignments_from_canvas()
    except exceptions.InvalidAccessToken or exceptions.ResourceDoesNotExist:
        print("Canvas API Failed! Using iCal...")
        canvas_url = get_calendar_url("Canvas")
        sync_assignments_from_ical(canvas_url)

    duration = time_module.perf_counter() - start_time
    print(f"Canvas assignment took {duration:.6f} seconds to sync!")

def sync_events():
    calendars = get_calendars()
    for calendar in calendars["calendars"]:
        start_time = time_module.perf_counter()
        print(f"Starting {calendar["name"]} Calendar sync...")

        sync_calendar(calendar["url"], calendar["name"])
        
        duration = time_module.perf_counter() - start_time
        print(f"{calendar["name"]} Calendar took {duration:.6f} seconds to sync!")        

def remove_old():
    load_dotenv()

    local_tz = ZoneInfo(os.getenv("TIME_ZONE"))
    today = datetime.now(local_tz).date()

    cutoff = today - timedelta(days=45)

    utc_cutoff = datetime.combine(
            cutoff, 
            time.min, 
            tzinfo=local_tz
        ).astimezone(timezone.utc).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
    
    removed_assignments = remove_assignments(cutoff, utc_cutoff)
    removed_envents = remove_events(cutoff, utc_cutoff)
    Logger.log(
        Logger.LogType.INFO,
        Logger.System.DATABASE,
        f"Removed {remove_assignments} assignments & {remove_events} events"
    )

def run_scheduler():
    init_db()
    NotificationWorker.initialize()
    Logger.initialize()

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

    scheduler.add_job(
        remove_old,
        "interval",
        minutes=60,
        next_run_time=datetime.now(),
        id="removal",
        max_instances=1,
        coalesce=True
    )

    scheduler.add_job(
        NotificationWorker.send_notification,
        "interval",
        minute=1,
        timezone="America/Chicago",
        id="daily_notifications",
        max_instances=1,
        replace_existing=True
    )

    Logger.log(
        Logger.LogType.INFO,
        Logger.System.SYSTEM,
        "Starting Scheduler..."
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        Logger.log(
            Logger.LogType.INFO,
            Logger.System.SYSTEM,
            "Shutting down scheduler..."
        )
        Logger.flush()

if __name__ == "__main__":
    run_scheduler()