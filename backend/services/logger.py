import os
import re
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from queue import Queue
from threading import Thread
from typing import ClassVar

class Colors():
    RESET = '\033[0m'

    # colors
    BLACK = '\033[30m'
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    BLUE = '\033[34m'
    MAGENTA = '\033[35m'
    CYAN = '\033[36m'
    GRAY = '\033[0;38;2;125;125;125;49m'
    WHITE = '\033[37m'

    @staticmethod
    def remove_color(text: str) -> str:
        ansi_regex = r'\x1b\[[0-9;]*m'
        return re.sub(ansi_regex, '', text)

class Logger():
    class LogType:
        INFO = f"{Colors.WHITE}[{Colors.RESET}INFO{Colors.WHITE}]{Colors.RESET}"
        WARNING = f"{Colors.WHITE}[{Colors.YELLOW}WARN{Colors.WHITE}]{Colors.RESET}"
        ERROR = f"{Colors.WHITE}[{Colors.RED}ERROR{Colors.WHITE}]{Colors.RESET}"

    class System:
        NOTIFICATION = f"{Colors.WHITE}[{Colors.MAGENTA}NOTIFICATION{Colors.WHITE}]{Colors.RESET}"
        DATABASE = f"{Colors.WHITE}[{Colors.CYAN}DATABASE{Colors.WHITE}]{Colors.RESET}"
        ICAL = f"{Colors.WHITE}[{Colors.BLUE}ICAL{Colors.WHITE}]{Colors.RESET}"
        SYSTEM = f"{Colors.WHITE}[SYSTEM]{Colors.RESET}"

    _initialized: ClassVar[bool] = False
    _path: ClassVar[str] | None
    _queue: ClassVar[Queue[dict[str, str]]]
    _thread: ClassVar[Thread]

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return

        load_dotenv()
        log_path = os.getenv("LOG_PATH")
        if log_path is not None:
            cls._path = str(Path(__file__).resolve().parent.parent.parent) + '\\' + str(log_path)
        else:
            cls._path = None

        cls._queue = Queue()
        cls._initialized = True

        from ..workers.log_worker import LogWorker # prevent circular import
        cls._thread = LogWorker.run()

    @classmethod
    def log(cls, log_type: str, system: str, message: str, use_colors: bool = True) -> None:
        if not cls._initialized:
            raise RuntimeError(
                "Call Logger.initialize() before Logger.log()"
            )
        
        if cls._path is not None and ".ans" not in cls._path:
            use_colors = False

        time = f"{Colors.WHITE}[{Colors.GRAY}{datetime.now()}{Colors.WHITE}]{Colors.RESET}"
        header = f"{time} {system} {log_type} "

        text = header
        for i, line in enumerate(message.split('\n')):
            indent = " " * len(Colors.remove_color(header)) if i > 0 else ""
            text += (indent + line + '\n')

        if not use_colors:
            text = Colors.remove_color(text)

        _log = {"message": text}
        cls._queue.put(_log)

    @classmethod
    def write_from_queue(cls) -> None:
        if not cls._initialized:
            raise RuntimeError(
                "Call Logger.initialize() before Logger.write_from_queue()"
            )
        
        message = cls._queue.get()
        try:
            if cls._path is not None:
                with open(cls._path, "a") as file:
                    file.write(message["message"])
            else:
                print(message["message"])
        finally:
            cls._queue.task_done()

    @classmethod
    def flush(cls) -> None:
        cls._queue.join()
    
if __name__ == "__main__":
    Logger.log(Logger.LogType.INFO, Logger.System.NOTIFICATION, "Test Notification\nThis is a test")