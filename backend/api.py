
import json
import os
import re
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from typing import Any
from fastapi import APIRouter, FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from . import database
from .services.logger import Logger
from .util import to_utc_string

CALENDAR_CONFIG_PATH: Path = Path(__file__).resolve().parents[1] / "calendars.json"

router = APIRouter(prefix="/api")


@router.get("/calendars")
def get_calendars() -> dict[str, Any]:
    """Expose display settings without exposing private calendar feed URLs."""
    try:
        with CALENDAR_CONFIG_PATH.open(encoding="utf-8") as file:
            config = json.load(file)
    except FileNotFoundError:
        raise HTTPException(
            status_code=404,
            detail={
                "code": "calendar_config_missing",
                "message": "calendars.json was not found."
            }
        ) from None

    calendars = []
    for calendar in config["calendars"]:
        display = {"name": calendar["name"]}
        color = calendar.get("color")
        if isinstance(color, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", color):
            display["color"] = color
        calendars.append(display)

    assignment_colors = {
        course: color
        for course, color in config.get("assignment_colors", {}).items()
        if isinstance(color, str) and re.fullmatch(r"#[0-9a-fA-F]{6}", color)
    }
    return {
        "calendars": calendars,
        "assignment_colors": assignment_colors,
        "timezone": os.getenv("TIME_ZONE") or "UTC"
    }

@router.get("/assignments")
def get_assignments(
    course_code: int | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    submitted: bool | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> list[dict[str, Any]]:
    return database.get_assignments(
        course_code=course_code,
        start=to_utc_string(start),
        end=to_utc_string(end),
        submitted=submitted,
        limit=limit,
        offset=offset
    )


@router.get("/events")
def get_events(
    calendar: str | None = None,
    name: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
    limit: int = Query(100, ge=1, le=500),
    offset: int = Query(0, ge=0)
) -> list[dict[str, Any]]:
    return database.get_events(
        calendar=calendar,
        name=name,
        start=to_utc_string(start),
        end=to_utc_string(end),
        limit=limit,
        offset=offset
    )


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    Logger.initialize()
    Logger.log(
        Logger.LogType.INFO,
        Logger.System.SYSTEM,
        "Starting Server..."
    )
    
    database.init_db()

    try:
        yield
    finally:
        Logger.log(
            Logger.LogType.INFO,
            Logger.System.SYSTEM,
            "Shutting Down Server..."
        )
        Logger.flush() # System is usually force-quit before this log is complete.


app = FastAPI(lifespan=lifespan)
app.include_router(router)

FRONTEND_PATH: Path = (
    Path(__file__).resolve().parent.parent
    / "frontend" / "index.html"
)


@app.get("/")
def frontend() -> FileResponse:
    return FileResponse(FRONTEND_PATH)


app.mount("/static", StaticFiles(directory=FRONTEND_PATH.parent), name="static")
