import os
import requests
from dotenv import load_dotenv
from typing import Any
from .logger import Logger

def send_notification(
    title: str,
    message: str,
    priority: int = 0,
    url: str | None = None,
    url_title: str | None = None
) -> dict[str, Any]:
    load_dotenv()

    data: dict[str, str | int | None] = {
        "token": os.getenv("PUSHOVER_APP_KEY"),
        "user": os.getenv("PUSHOVER_USER_KEY"),
        "title": title,
        "message": message,
        "priority": priority
    }

    if url:
        data["url"] = url
        if url_title:
            data["url_title"] = url_title

    response = requests.post(
        "https://api.pushover.net/1/messages.json",
        data=data,
        timeout=15
    )

    # Logging
    if response.status_code == 200:
        log_type = Logger.LogType.INFO
    elif 500 <= response.status_code:
        log_type = Logger.LogType.WARNING
    else:
        log_type = Logger.LogType.ERROR

    Logger.log(
        log_type=log_type,
        system=Logger.System.NOTIFICATION,
        message=f"Sending Notification:\n{title}\n{message}\nResponse: {response.json()}"
    )

    return response.json()

if __name__ == "__main__":
    Logger.initialize()
    send_notification(
        title="Calendar Test",
        message="Your notification system is working!"
    )
    Logger.flush()