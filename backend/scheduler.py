from datetime import datetime
from apscheduler.schedulers.blocking import BlockingScheduler

from .database import init_db 
from .services.logger import Logger
from .workers.calendar_worker import CalendarWorker
from .workers.canvas_worker import CanvasWorker
from .workers.log_worker import LogWorker
from .workers.notification_worker import NotificationWorker      

def run_scheduler():
    init_db()
    CalendarWorker.initialize()
    CanvasWorker.initialize()
    Logger.initialize()
    NotificationWorker.initialize()

    scheduler = BlockingScheduler()

    scheduler.add_job(
        LogWorker.log_ram_usage,
        "interval",
        minutes=1,
        next_run_time=datetime.now(),
        id="ram_usage",
        max_instances=1,
        coalesce=True
    )

    scheduler.add_job(
        CanvasWorker.sync_assignments,
        "interval",
        minutes=5,
        next_run_time=datetime.now(),
        id="assignments",
        max_instances=1,
        coalesce=True
    )

    scheduler.add_job(
        CalendarWorker.sync_events,
        "interval",
        minutes=5,
        next_run_time=datetime.now(),
        id="events",
        max_instances=1,
        coalesce=True
    )

    scheduler.add_job(
        CalendarWorker.remove_old_events,
        "interval",
        minutes=60,
        next_run_time=datetime.now(),
        id="remove_events",
        max_instances=1,
        coalesce=True
    )

    scheduler.add_job(
        CanvasWorker.remove_old_assignments,
        "interval",
        minutes=60,
        next_run_time=datetime.now(),
        id="remove_assignments",
        max_instances=1,
        coalesce=True
    )

    scheduler.add_job(
        NotificationWorker.send_notification,
        "interval",
        minutes=1,
        timezone="America/Chicago",
        id="daily_notifications",
        max_instances=1,
        replace_existing=True
    )

    Logger.log(
        Logger.LogType.INFO,
        Logger.System.SYSTEM,
        "Starting Scheduler..."
    )

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        pass
    finally:
        Logger.log(
            Logger.LogType.INFO,
            Logger.System.SYSTEM,
            "Shutting down scheduler..."
        )
        Logger.flush()

if __name__ == "__main__":
    run_scheduler()