import psutil
from pathlib import Path
from threading import Thread
from typing import NoReturn

from ..services.logger import Logger

class LogWorker:
    @staticmethod
    def _process_queue() -> NoReturn:
        while True:
            Logger.write_from_queue()

    @staticmethod
    def run() -> Thread:
        thread = Thread(
            target=LogWorker._process_queue,
            name="logger",
            daemon=True
        )
        thread.start()
        return thread

    @staticmethod
    def log_ram_usage() -> None:
        process = psutil.Process()
        root = process

        # Include the API and launcher when started through this project's run.py.
        for parent in process.parents():
            try:
                if (
                    Path(parent.cwd()).resolve() == Path(__file__).resolve().parents[2]
                    and any(Path(arg).name == "run.py" for arg in parent.cmdline()[1:])
                ):
                    root = parent
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        try:
            processes = [root] + root.children(recursive=True)
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            processes = [process]

        total_ram = 0
        for proc in processes:
            try:
                total_ram += proc.memory_info().rss
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        Logger.log(
            Logger.LogType.INFO,
            Logger.System.SYSTEM,
            f"Total RAM usage: {total_ram / (1024 ** 2):.2f} MB"
        )
