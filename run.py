import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

from .backend.services.logger import Logger

ROOT = Path(__file__).resolve().parent
URL = "http://localhost:8000/"

def open_frontend(processes, timeout: float = 15) -> None:
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes): # Ensure all processes are running
            return

        try:
            with urlopen(URL, timeout=1) as response: # Check the server
                ready = response.status == 200
        except (URLError, OSError): # Cannot connect to Server
            ready = False

        if ready:
            if not webbrowser.open_new(URL): # Open the frontend in default browser
                print(f"Open the frontend at {URL}")
            return

        time.sleep(0.25)

    print(f"Frontend startup timed out. Once the API is ready, open {URL}") # prints if failed to open


def main():
    processes = []

    try:
        # Start FastAPI
        api = subprocess.Popen(
            [
                sys.executable, "-m", "uvicorn",
                "backend.api:app",
                "--host", "0.0.0.0",
                "--port", "8000"
            ],
            cwd=ROOT
        )
        processes.append(api)

        # Start scheduler
        scheduler = subprocess.Popen(
            [
                sys.executable, "-m",
                "backend.scheduler"
            ],
            cwd=ROOT
        )
        processes.append(scheduler)

        open_frontend(processes) # Opens the browser

        # Keep launcher alive while both processes run
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        Logger.log(
            Logger.LogType.INFO,
            Logger.System.SYSTEM,
            "Shutting Down Server..."
        )
        Logger.flush() # This is to replace the call in api.py line 67

    finally:
        for process in processes:
            if process.poll() is None:
                process.terminate()

        for process in processes:
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()


if __name__ == "__main__":
    main()
