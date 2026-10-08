import requests
from icalendar import Calendar
from ..database import save_assignment

def fetch_events(url: str) -> list[dict]:
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    calendar = Calendar.from_ical(response.content)
    events = []

    for event in calendar.walk("VEVENT"):
        start = event.decoded("DTSTART")

        end = (
            event.decoded("DTEND")
            if event.get("DTEND")
            else None
        )

        events.append({
            "uid": str(event.get("UID", "")),
            "title": str(event.get("SUMMARY", "")),
            "description": str(event.get("DESCRIPTION", "")),
            "location": str(event.get("LOCATION", "")),
            "start": start,
            "end": end,
        })

    return events

def fetch_assignments_from_ical(canvas_url: str):
    events = fetch_events(canvas_url)

    for event in events:
        print(f"UID: {event["uid"]}")

def sync_calendar(url: str):
    pass