import json
from pathlib import Path
from .database import init_db, print_assignments
from .services.ical_sync import fetch_assignments_from_ical

CALENDAR_PATH = Path(__file__).resolve().parent.parent / "calendars.json"

def get_calendar_url(name: str) -> str:
    with open(CALENDAR_PATH, "r", encoding="utf-8") as file:
        calendars = json.load(file)

    for calendar in calendars["calendars"]:
        if calendar["name"] == name:
            return calendar["url"]

    raise ValueError(f"Calendar '{name}' not found")

def sync_assignments():
    print("Starting Canvas assignment sync...")

    canvas_url = get_calendar_url("Canvas")
    fetch_assignments_from_ical(canvas_url)

    print("Canvas assignment sync complete!")


if __name__ == "__main__":
    init_db()
    sync_assignments()
    print_assignments()