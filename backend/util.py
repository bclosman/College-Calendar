from datetime import datetime, timezone

def to_utc_string(value: datetime | None) -> str | None:
    if value is None:
        return None

    if value.tzinfo is None:
        raise RuntimeError("Object has no timezone!")

    return value.astimezone(timezone.utc).strftime(
        "%Y-%m-%dT%H:%M:%SZ"
    )