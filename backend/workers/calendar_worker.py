import json
import time as time_module
from datetime import date, timedelta
from pathlib import Path
from typing import ClassVar

from ..database import remove_events
from ..services.ical_sync import sync_calendar
from ..services.logger import Logger

class CalendarWorker:
    _REMOVAL_CUTOFF: ClassVar[int] = 46 # Days
    _calendars_path: ClassVar[Path | None] = None
    _initialized: ClassVar[bool] = False

    @classmethod
    def __get_calendars(cls) -> list[dict[str, str]] | None:
        try:
            with open(cls._calendars_path, "r", encoding="utf-8") as file:
                calendars: dict[str, list[dict[str, str]]] = json.load(file)
        except:
            return None
        return calendars["calendars"]

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return
        
        cls._calendars_path = Path(__file__).resolve().parents[2] / "calendars.json"
        cls._initialized = True

    @classmethod
    def get_calendar_url(cls, name: str) -> str:
        if not cls._initialized:
            raise RuntimeError("Call CalendarWorker.initialize() before CalendarWorker.get_calendar_url()")
        
        calendars = cls.__get_calendars()
        if calendars is None:
            return ""
        for calendar in calendars:
            if calendar["name"] == name:
                return calendar["url"]

        raise ValueError(f"Calendar '{name}' not found")
    
    @classmethod
    def sync_events(cls) -> None:
        if not cls._initialized:
            raise RuntimeError("Call CalendarWorker.initialize() before CalendarWorker.sync_events()")
        
        calendars = cls.__get_calendars()
        if calendars is None:
            return
        for calendar in calendars:
            start_time = time_module.perf_counter()

            sync_calendar(calendar["url"], calendar["name"])
            
            duration = time_module.perf_counter() - start_time
            Logger.log(
                Logger.LogType.INFO,
                Logger.System.DATABASE,
                f"{calendar["name"]} Calendar took {duration:.6f} seconds to sync!"
            )  

    @classmethod
    def remove_old_events(cls) -> None:
        if not cls._initialized:
            raise RuntimeError("Call CalendarWorker.initialize() before CalendarWorker.remove_old_events()")
        
        today = date.today()
        cutoff_date = today - timedelta(days=cls._REMOVAL_CUTOFF)
        
        count = remove_events(cutoff_date)
        Logger.log(
            Logger.LogType.INFO,
            Logger.System.DATABASE,
            f"Removed {count} events."
        )

if __name__ == "__main__":
    Logger.initialize()
    CalendarWorker.initialize()
    Logger.flush()