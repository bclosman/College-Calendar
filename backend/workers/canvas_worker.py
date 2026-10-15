import time as time_module
from datetime import date, timedelta
from typing import ClassVar

from ..database import remove_assignments
from ..services.canvas_sync import sync_assignments_from_canvas
from ..services.ical_sync import sync_assignments_from_ical
from ..services.logger import Logger
from .calendar_worker import CalendarWorker

class CanvasWorker:
    _initialized: ClassVar[bool] = False
    _REMOVAL_CUTOFF: ClassVar[int] = 46 # Days

    @classmethod
    def initialize(cls) -> None:
        if cls._initialized:
            return
        
        CalendarWorker.initialize()
        cls._initialized = True

    @classmethod
    def sync_assignments(cls) -> None:
        if not cls._initialized:
            raise RuntimeError("Call CanvasWorker.initialize() before CanvasWorker.sync_assignments()!")
        
        start_time = time_module.perf_counter()

        try:
            sync_assignments_from_canvas()
        except:
            Logger.log(
                Logger.LogType.WARNING,
                Logger.System.DATABASE,
                "Canvas API Failed! Using iCal..."
            )
            canvas_url = CalendarWorker.get_calendar_url("Canvas")
            sync_assignments_from_ical(canvas_url)

        duration = time_module.perf_counter() - start_time
        Logger.log(
                Logger.LogType.INFO,
                Logger.System.DATABASE,
                f"Canvas took {duration:.6f} seconds to sync!"
            )
        
    @classmethod
    def remove_old_assignments(cls) -> None:
        if not cls._initialized:
            raise RuntimeError("Call CanvasWorker.initialize() before CanvasWorker.remove_old_assignments()!")
        
        today = date.today()
        cutoff_date = today - timedelta(days=cls._REMOVAL_CUTOFF)
        
        count = remove_assignments(cutoff_date)
        Logger.log(
            Logger.LogType.INFO,
            Logger.System.DATABASE,
            f"Removed {count} assignments."
        )