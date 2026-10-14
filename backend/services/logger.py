import os
import re
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path
from queue import Queue

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
    def remove_color(text: str):
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
        SYSTEM = f"{Colors.WHITE}[SYSTEM]{Colors.RESET}"

    _initialized = False

    @classmethod
    def initialize(cls):
        if cls._initialized:
            return

        load_dotenv()
        cls._path = str(Path(__file__).resolve().parent.parent.parent) + '\\' + str(os.getenv("LOG_PATH"))
        cls._queue = Queue()
        cls._initialized = True

    @classmethod
    def log(cls, log_type: Logger.LogType, system: Logger.System, message: str, use_colors=True):
        if not cls._initialized:
            raise RuntimeError(
                "Call Logger.initialize() before Logger.log()"
            )
        
        if ".ans" not in cls._path:
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
    def write_from_queue(cls):
        if not cls._initialized:
            raise RuntimeError(
                "Call Logger.initialize() before Logger.log()"
            )
        
        _log = cls._queue.get()
        with open(cls._path, "a") as file:
            file.write(_log["message"])
    
if __name__ == "__main__":
    Logger.log(Logger.LogType.INFO, Logger.System.NOTIFICATION, "Test Notification\nThis is a test")