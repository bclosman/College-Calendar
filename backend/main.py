
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse

from backend import database
from backend.api import router

from .services.logger import Logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs when the server starts
    database.init_db()

    yield

    # Runs when the server shuts down
    Logger.log(
        Logger.LogType.INFO,
        Logger.System.SYSTEM,
        "Shutting Down..."
    )


app = FastAPI(lifespan=lifespan)

# Register API endpoints
app.include_router(router)

# Location of frontend HTML
FRONTEND_PATH = (
    Path(__file__).resolve().parent.parent
    / "frontend" / "index.html"
)

# Serve frontend at root URL
@app.get("/")
def frontend():
    return FileResponse(FRONTEND_PATH)