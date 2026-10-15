
from datetime import datetime, timezone
from fastapi import APIRouter, HTTPException, Query

from .database import get_assignments, get_events
from .util import to_utc_string

router = APIRouter(prefix="/api")

@router.get("/assignments")
def get_assignments(
    course_code: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    submitted: bool | None = None,
    limit: int = Query(100, ge=1, le=500)
):
    return get_assignments(
        course_code=course_code,
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
    return get_events(
        calendar=calendar,
        name=name,
        start=to_utc_string(start),
        end=to_utc_string(end),
        limit=limit
    )
