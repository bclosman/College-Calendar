import re
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
            "url": str(event.get("URL", ""))
        })

    return events

def fetch_assignments_from_ical(canvas_url: str):
    events = fetch_events(canvas_url)

    for event in events:
        if "assignment" in event["uid"]:
            split = re.split(r' \(| \[', event["title"], maxsplit=1)
            assignment_title = split[0]

            course = re.search(r"\b([A-Z]+)-(\d+)\b", split[1])
            course_name = course.group(0)
            course_id = course.group(2)

            due_date = event["start"]
            url = event["url"]

            save_assignment({
                "uid": event["uid"],
                "course_id": course_id,
                "course_name": course_name,
                "name": assignment_title,
                "due_at": due_date,
                "submitted": False,
                "url": url
            })

def sync_calendar(url: str):
    pass