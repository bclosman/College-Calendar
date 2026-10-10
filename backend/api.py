
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

from backend import database

router = APIRouter(prefix="/api")


def to_utc_string(value: datetime | None):
    if value is None:
        return None

    if value.tzinfo is None:
        raise HTTPException(422, "Timezone is required")

    return value.astimezone(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )


@router.get("/assignments")
def get_assignments(
    course_id: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    submitted: bool | None = None,
    limit: int = Query(100, ge=1, le=500)
):
    return database.get_assignments(
        course_id=course_id,
        start=to_utc_string(start),
        end=to_utc_string(end),
        submitted=submitted,
        limit=limit
    )


@router.get("/events")
def get_events(
    calendar: str | None = None,
    name: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(100, ge=1, le=500)
):
    return database.get_events(
        calendar=calendar,
        name=name,
        start=to_utc_string(start),
        end=to_utc_string(end),
        limit=limit
    )
