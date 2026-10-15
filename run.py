import psutil
import subprocess
import sys
import time
from pathlib import Path

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
