
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

app = FastAPI()

@app.get("/api/assignments")
def get_assignments():
    return [
        {
            "id": "example-1",
            "course": "CSCE 235",
            "name": "Homework 4",
            "due_at": "2026-10-12T23:59:00-05:00",
            "completed": False
        },
        {
            "id": "example-2",
            "course": "MATH 208",
            "name": "Quiz 6",
            "due_at": "2026-10-14T23:59:00-05:00",
            "completed": False
        }
    ]

# Keep this after the API routes
app.mount(
    "/",
    StaticFiles(directory="frontend", html=True),
    name="frontend"
)
