
from datetime import datetime, timezone
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Query

from backend import database


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs when the server starts
    database.init_db()

    yield

    # Runs when the server shuts down
    print("Server shutting down")


app = FastAPI(lifespan=lifespan)

def to_utc_string(value: datetime | None):
    if value is None:
        return None

    if value.tzinfo is None:
        raise HTTPException(422, "Timezone is required")

    return value.astimezone(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )

@app.get("/api/assignments")
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
