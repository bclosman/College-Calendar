
from contextlib import asynccontextmanager
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, FastAPI, Query
from fastapi.responses import FileResponse

from . import database
from .services.logger import Logger
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
    return database.get_assignments(
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
    return database.get_events(
        calendar=calendar,
        name=name,
        start=to_utc_string(start),
        end=to_utc_string(end),
        limit=limit
    )


@asynccontextmanager
async def lifespan(app: FastAPI):
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

FRONTEND_PATH = (
    Path(__file__).resolve().parent.parent
    / "frontend" / "index.html"
)


@app.get("/")
def frontend():
    return FileResponse(FRONTEND_PATH)
