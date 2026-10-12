import os
import requests
from dotenv import load_dotenv

def send_notification(title, message, priority=0, url=None, url_title=None):
    load_dotenv()

    data = {
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

    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    send_notification(
        title="Calendar Test",
        message="Your notification system is working!"
    )