import json
import os
from datetime import date, datetime, time, timedelta, timezone
from dotenv import load_dotenv
from pathlib import Path
from zoneinfo import ZoneInfo

from ..database import get_assignments
from ..services.logger import Logger
from ..services.notification import send_notification
from ..util import to_utc_string

class NotificationWorker:
    _CHAR_LIMIT = 40

    _canvas_url = ""
    _initialized = False
    _time_zone = ZoneInfo("UTC")
    _schedule_path = ""

    @classmethod
    def __build_message(cls, assignments: list[dict]) -> str: # Private Method
        message = ""
        for assignment in assignments:
            course_name = assignment["course_name"]
            assignment_name = assignment["name"]

            if len(assignment_name) > cls._CHAR_LIMIT:
                assignment_name = assignment_name[:cls._CHAR_LIMIT - 3] + "..." 

            due_at = assignment["due_at"]
            if len(due_at) == 10: # due_at does not have a time associated, default to 11:59 PM
                due_at = datetime.combine(
                    date.fromisoformat(due_at),
                    time(23, 59),
                    tzinfo=cls._time_zone
                )
            else:
                due_at = datetime.fromisoformat(due_at.replace("Z", "+00:00")).astimezone(cls._time_zone)

            message_line = f"\n{course_name}({due_at.strftime("%I:%M%p")}): {assignment_name}"

            if len(message_line) > cls._CHAR_LIMIT + 1: # Accounts for leading \n
                message_line = message_line[:cls._CHAR_LIMIT - 2] # Accounts for leading \n
                message_line += "..."
            message += message_line

        if len(assignments) > 3:
            message += "\n..."

        return message[1:] # Accounts for initial \n

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return
        load_dotenv()
        cls._canvas_url = os.getenv("CANVAS_URL")
        cls._time_zone = ZoneInfo(os.getenv("TIME_ZONE"))
        cls._initialized = True
        cls._schedule_path = Path(__file__).resolve().parents[2] / "notification_schedule.json"

    @classmethod
    def __week_notification(cls) -> None: # Private Method
        today = datetime.now(cls._time_zone)
        start = to_utc_string(datetime.combine(
            today,
            time.min,
            tzinfo=cls._time_zone
        ))
        end = to_utc_string(datetime.combine(
            today + timedelta(days=6),
            time.max,
            tzinfo=cls._time_zone
        ))

        assignments = get_assignments(
            start=start,
            end=end,
            submitted=False
        )

        if len(assignments) > 0:
            message = f"You have {len(assignments)} assignment{"s" if len(assignments) == 1 else ""} due this week!\n" 
            message += cls.__build_message(assignments)

            if assignments == 1:
                url = assignments[0]["url"]
                url_title = "View Assignment"
            else:
                url = cls._canvas_url
                url_title = "View Assignments"

            send_notification(
                title="Weekly Assignemtns",
                message=message,
                url=url,
                url_title=url_title
            )
        else:
            send_notification(
                title="Weekly Assignemtns",
                message="You have no assignments due for 7 days!",
                url=url,
                url_title=url_title
            )

    @classmethod
    def __day_notification(cls) -> None: # Private Method
        today = datetime.now(cls._time_zone)
        start = to_utc_string(datetime.combine(
            today,
            time.min,
            tzinfo=cls._time_zone
        ))
        end = to_utc_string(datetime.combine(
            today,
            time.max,
            tzinfo=cls._time_zone
        ))

        assignments = get_assignments(
            start=start,
            end=end,
            submitted=False
        )

        if len(assignments) > 0:
            message = cls.__build_message(assignments)

            if assignments == 1:
                url = assignments[0]["url"]
                url_title = "View Assignment"
            else:
                url = cls._canvas_url
                url_title = "View Assignments"

            send_notification(
                title="Daily Assignemtns",
                message=message,
                url=url,
                url_title=url_title
            )
        else:
            cls.__week_notification()

    @classmethod
    def send_notification(cls) -> None:
        if not cls._initialized:
            raise RuntimeError(
                "Call NotificationWorker.initialize() before NotificationWorker.send_notification()"
            )
        
        now = datetime.now(cls._time_zone)
        current_time = now.strftime("%H:%M") # Get time as HH:MM
        day = ("mon", "tue", "wed", "thu", "fri", "sat", "sun")[now.weekday()] # Get day

        with open(cls._schedule_path, "r", encoding="utf-8") as file:
            schedule = json.load(file)

        daily = schedule["daily"]
        if day in daily["days"] and current_time in daily["times"]:
            cls.__day_notification()

        weekly = schedule["weekly"]
        if day in weekly["days"] and current_time in weekly["times"]:
            cls.__week_notification()

if __name__ == "__main__":
    Logger.initialize()
    NotificationWorker.initialize()
    NotificationWorker._NotificationWorker__day_notification()
    Logger.flush()