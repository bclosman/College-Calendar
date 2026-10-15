from threading import Thread
from time import sleep

from ..services.logger import Logger

class LogWorker:
    @staticmethod
    def _process_queue():
        while True:
            Logger.write_from_queue()

    @staticmethod
    def run():
        thread = Thread(
            target=LogWorker._process_queue,
            name="logger",
            daemon=True
        )
        thread.start()
        return thread