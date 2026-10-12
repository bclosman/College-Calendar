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
from .services.notification import send_notification

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

def daily_notification():
    load_dotenv()
    CHAR_LIMIT = 40

    time_zone = ZoneInfo(os.getenv("TIME_ZONE"))
    today = datetime.now(time_zone).date()
    start_local = datetime.combine(
        today,
        time.min,
        tzinfo=time_zone
    )
    end_local = datetime.combine(
        today + timedelta(days=6),
        time.max,
        tzinfo=time_zone
    )
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    
    assignments = get_assignments(
        start=start_utc, 
        end=end_utc, 
        submitted=False
    )
    
    if len(assignments) != 0:
        message = ""
        for assignment in assignments[:3]:
            course_name = assignment["course_name"]
            assignment_name = assignment["name"]

            if len(assignment_name) > CHAR_LIMIT:
                assignment_name = assignment_name[:CHAR_LIMIT - 3] + "..." 

            due_at = assignment["due_at"]
            if len(due_at) == 10:
                due_at = datetime.combine(
                    today,
                    time.max,
                    tzinfo=time_zone
                )
            else:
                due_at = datetime.fromisoformat(due_at.replace("Z", "+00:00")).astimezone(time_zone)

            message_line = f"\n{course_name}({due_at.strftime("%I:%M%p")}): {assignment_name}"
            if len(message_line) > CHAR_LIMIT + 1:
                message_line = message_line[:CHAR_LIMIT - 2]
                message_line += "..."
            message += message_line

        if len(assignments) > 3:
            message += "..."

        if len(assignments) == 0:
            url = assignment["url"]
            url_title = "View Assignment"
        else:
            url = os.getenv("CANVAS_URL")
            url_title = "View Assignments"
        
        send_notification(
            title="Daily Assignments",
            message=message[1:],
            url=url,
            url_title=url_title
        )

def weekly_notification():
    load_dotenv()

    time_zone = ZoneInfo(os.getenv("TIME_ZONE"))
    today = datetime.now(time_zone).date()
    start_local = datetime.combine(
        today,
        time.min,
        tzinfo=time_zone
    )
    end_local = datetime.combine(
        today + timedelta(days=6),
        time.max,
        tzinfo=time_zone
    )
    start_utc = start_local.astimezone(timezone.utc)
    end_utc = end_local.astimezone(timezone.utc)
    
    assignments = get_assignments(
        start=start_utc, 
        end=end_utc, 
        submitted=False
    )
    assignments = [assignments[0]]

    if len(assignments) > 0:
        if len(assignments) == 1:
            message = "You have 1 assignment due this week!"
            url = assignments[0]["url"]
            url_title = "View Assignment"
        else:
            message = f"You have {len(assignments)} assignments due this week!"
            url = os.getenv("CANVAS_URL")
            url_title = "View Assignments"

        send_notification(
            title="Weekly Assignments",
            message=message,
            url=url,
            url_title=url_title
        )
    else:
        send_notification(
            title="Weekly Assignments",
            message="You have no assignments due this week!",
        )        

def remove_old():
    print("Removing old objects...")
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
    
    remove_assignments(cutoff, utc_cutoff)
    remove_events(cutoff, utc_cutoff)
    print("Removal Complete!")

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
        daily_notification,
        "cron",
        hour="8,12,18,21",
        minute=0,
        timezone="America/Chicago",
        id="daily_notifications",
        max_instances=1,
        replace_existing=True
    )

    scheduler.add_job(
        daily_notification,
        "cron",
        day_of_week="sat",
        hour="8,20",
        minute=0,
        timezone="America/Chicago",
        id="weekly_notifications",
        max_instances=1,
        replace_existing=True
    )

    send_notification(
        title="System Uodate",
        message="Calendar server up and running!"
    )
    scheduler.start()

if __name__ == "__main__":
    run_scheduler()