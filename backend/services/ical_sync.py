import re
from urllib.parse import urlparse
import recurring_ical_events
import requests
from datetime import date, datetime, timedelta, timezone
from icalendar import Calendar
from ..database import save_assignment, save_events

def format_date(_date: any):
    if isinstance(_date, datetime):
        return _date.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    elif isinstance(_date, date):
        return _date.isoformat()
    elif _date is None:
        return None
    else:
        raise ValueError("Error: Invalid Date Format")


def fetch_events(url: str) -> list[dict]:
    response = requests.get(url, timeout=20)
    response.raise_for_status()

    calendar = Calendar.from_ical(response.content)
    events = []

    # Define how far to retrieve events
    today = date.today()
    start_date = today - timedelta(days=30)
    end_date = today + timedelta(days=120)

    # Identify recurring event series
    recurring_uids = {
        str(event.get("UID"))
        for event in calendar.walk("VEVENT")
        if (
            event.get("RRULE") is not None
            or event.get("RDATE") is not None
            or event.get("RECURRENCE-ID") is not None
        )
    }

    # Expand recurring events into individual occurrences
    occurrences = recurring_ical_events.of(
        calendar
    ).between(start_date, end_date)

    for event in occurrences:

        uid = str(event.get("UID", ""))

        start = event.decoded("DTSTART")

        end = (
            event.decoded("DTEND")
            if event.get("DTEND")
            else None
        )

        # Each recurring occurrence needs a unique ID
        if uid in recurring_uids:
            uid += f" : {start}"

        events.append({
            "uid": uid,
            "title": str(event.get("SUMMARY", "")),
            "description": str(event.get("DESCRIPTION", "")),
            "location": str(event.get("LOCATION", "")),
            "start": start,
            "end": end,
            "url": str(event.get("URL", ""))
        })

    return events


def sync_assignments_from_ical(canvas_url: str):
    events = fetch_events(canvas_url)

    for event in events:
        if "assignment" in event["uid"]:
            split = re.split(r' \(| \[', event["title"], maxsplit=1)
            assignment_title = split[0]

            course = re.search(
                r"\b([A-Z]+)-(\d+)\.(\d+)\.(\d+)\b",
                split[1]
            )
            course_name = f"{course.group(1)}-{course.group(2)}"
            course_code = course.group(0)

            due_date = format_date(event["start"])
            
            url = event["url"]
            assignment_id = int(re.search(r"assignment_(\d+)", urlparse(url).fragment).group(1))
            course_id = int(re.search(r"course_(\d+)", urlparse(url).query).group(1))
            

            save_assignment({
                "id": assignment_id,
                "course_code": course_code,
                "course_name": course_name,
                "course_id": course_id,
                "name": assignment_title,
                "due_at": due_date,
                "submitted": False,
                "url": url
            })

def sync_calendar(url: str, calendar_name: str):
    events = fetch_events(url)
    save_events(calendar_name, events)