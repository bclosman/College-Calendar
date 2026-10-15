import os
import re
from canvasapi import Canvas
from datetime import timedelta, datetime, timezone
from dotenv import load_dotenv
from ..database import save_assignment
from .ical_sync import format_date

def sync_assignments_from_canvas() -> None:
    load_dotenv()

    CANVAS_URL = os.getenv("CANVAS_URL")
    CANVAS_API_KEY = os.getenv("CANVAS_API_KEY")

    canvas = Canvas(CANVAS_URL, CANVAS_API_KEY)
    courses = canvas.get_courses(
        enrollment_type="student",
        enrollment_state="active"
    )

    today = datetime.now(timezone.utc)
    start_date = today - timedelta(days=45)
    end_date = today + timedelta(days=120)

    for course in courses:
        assignments = course.get_assignments(include=["submission"])
        for assignment in assignments:
            if assignment.due_at is None:
                continue

            due_at = datetime.fromisoformat(
                assignment.due_at.replace("Z", "+00:00")
            )

            if not start_date <= due_at <= end_date:
                continue

            name = course.course_code[:8]

            submission = getattr(assignment, "submission", None)
            save_assignment({
                "id": assignment.id,
                "course_code": course.course_code,
                "course_name": name,
                "course_id": course.id,
                "name": assignment.name,
                "due_at": due_at.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "submitted": int(submission is not None and submission.get("submitted_at") is not None),
                "url": assignment.html_url
            })

if __name__ == "__main__":
    sync_assignments_from_canvas()