import json
import time
from pathlib import Path
from .database import init_db, print_events
from .services.ical_sync import sync_assignments_from_ical, sync_calendar

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

if __name__ == "__main__":
    init_db()
    
    while True:
        sync_assignments()
        sync_events()

        time.sleep(60 * 5)