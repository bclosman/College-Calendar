from contextlib import asynccontextmanager
from fastapi import FastAPI

from backend import database

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs when the server starts
    database.init_db()

    yield

    # Runs when the server shuts down
    print("Server shutting down")


app = FastAPI(lifespan=lifespan)

for route in app.routes:
    print(route.path)