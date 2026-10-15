import psutil
import subprocess
import sys
import time
import webbrowser
from pathlib import Path
from urllib.error import URLError
from urllib.request import urlopen

ROOT = Path(__file__).resolve().parent

def get_memory_usage(processes):
    total_ram = 0

    for process in processes:
        if process.poll() is not None:
            continue

        try:
            parent = psutil.Process(process.pid)
            children = parent.children(recursive=True)

            for proc in [parent] + children:
                total_ram += proc.memory_info().rss

        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

    return total_ram / (1024 ** 2)

def open_frontend(processes, timeout: float = 15) -> None:
    url = "http://127.0.0.1:8000/"
    deadline = time.monotonic() + timeout

    while time.monotonic() < deadline:
        if any(process.poll() is not None for process in processes):
            return

        try:
            with urlopen(url, timeout=1) as response:
                ready = response.status == 200
        except (URLError, OSError):
            ready = False

        if ready:
            if not webbrowser.open_new(url):
                print(f"Open the frontend at {url}")
            return

        time.sleep(0.25)

    print(f"Frontend startup timed out. Once the API is ready, open {url}")


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

        open_frontend(processes)

        # Keep launcher alive while both processes run
        while all(p.poll() is None for p in processes):
            time.sleep(0.5)
    except KeyboardInterrupt:
        pass

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
