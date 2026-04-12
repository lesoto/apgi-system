"""
Date and time utilities for consistent timestamp handling.

Provides timezone-aware datetime functions to avoid timezone comparison issues.
Includes utilities for simulation time tracking, duration formatting, and
timestamp parsing for the APGI system.
"""

import re
from datetime import datetime, timedelta, timezone
from typing import Optional, Union


def utc_now() -> datetime:
    """
    Get current UTC time as timezone-aware datetime.

    Returns:
        datetime: Current UTC time with timezone information
    """
    return datetime.now(timezone.utc)


def format_timestamp(dt: Union[datetime, None]) -> Union[str, None]:
    """
    Format datetime as ISO string with timezone information.

    Args:
        dt: datetime object or None

    Returns:
        ISO formatted timestamp string or None
    """
    if dt is None:
        return None
    return dt.isoformat()


def format_timestamp_utc(dt: Union[datetime, None]) -> Union[str, None]:
    """
    Format datetime as ISO string with 'Z' suffix for UTC.

    Args:
        dt: datetime object or None

    Returns:
        ISO formatted timestamp string with 'Z' suffix or None
    """
    if dt is None:
        return None
    if dt.tzinfo is None:
        # Convert naive datetime to UTC
        dt = dt.replace(tzinfo=timezone.utc)
    return dt.isoformat().replace("+00:00", "Z")


def parse_timestamp(timestamp: str) -> Optional[datetime]:
    """
    Parse ISO timestamp string to datetime object.

    Args:
        timestamp: ISO formatted timestamp string

    Returns:
        datetime object or None if parsing fails
    """
    if not timestamp:
        return None

    # Try common ISO formats
    formats = [
        "%Y-%m-%dT%H:%M:%S.%f%z",  # ISO with microseconds and timezone
        "%Y-%m-%dT%H:%M:%S%z",  # ISO with timezone
        "%Y-%m-%dT%H:%M:%S.%f",  # ISO with microseconds, no timezone
        "%Y-%m-%dT%H:%M:%S",  # ISO without timezone
        "%Y-%m-%d %H:%M:%S",  # Space separated
        "%Y-%m-%d",  # Date only
    ]

    for fmt in formats:
        try:
            return datetime.strptime(timestamp, fmt)
        except ValueError:
            continue

    return None


def format_duration_ms(duration_ms: float) -> str:
    """
    Format duration in milliseconds to human-readable string.

    Args:
        duration_ms: Duration in milliseconds

    Returns:
        Human-readable duration string (e.g., "1h 23m 45.6s")
    """
    if duration_ms < 0:
        duration_ms = 0

    # Convert to seconds
    total_seconds = duration_ms / 1000.0

    hours = int(total_seconds // 3600)
    minutes = int((total_seconds % 3600) // 60)
    seconds = total_seconds % 60

    if hours > 0:
        return f"{hours}h {minutes}m {seconds:.1f}s"
    elif minutes > 0:
        return f"{minutes}m {seconds:.1f}s"
    elif seconds >= 1:
        return f"{seconds:.1f}s"
    else:
        return f"{duration_ms:.0f}ms"


def format_duration_seconds(duration_sec: float) -> str:
    """
    Format duration in seconds to human-readable string.

    Args:
        duration_sec: Duration in seconds

    Returns:
        Human-readable duration string
    """
    return format_duration_ms(duration_sec * 1000)


def get_elapsed_since(start_dt: datetime) -> str:
    """
    Get elapsed time since a given datetime as human-readable string.

    Args:
        start_dt: Start datetime

    Returns:
        Human-readable elapsed time string
    """
    now = utc_now()
    elapsed_ms = (now - start_dt).total_seconds() * 1000
    return format_duration_ms(elapsed_ms)


def get_elapsed_ms(start_dt: datetime) -> float:
    """
    Get elapsed milliseconds since a given datetime.

    Args:
        start_dt: Start datetime

    Returns:
        Elapsed milliseconds
    """
    now = utc_now()
    return (now - start_dt).total_seconds() * 1000


def get_elapsed_seconds(start_dt: datetime) -> float:
    """
    Get elapsed seconds since a given datetime.

    Args:
        start_dt: Start datetime

    Returns:
        Elapsed seconds
    """
    now = utc_now()
    return (now - start_dt).total_seconds()


def to_timestamp_ms(dt: datetime) -> int:
    """
    Convert datetime to Unix timestamp in milliseconds.

    Args:
        dt: datetime object

    Returns:
        Unix timestamp in milliseconds
    """
    return int(dt.timestamp() * 1000)


def from_timestamp_ms(timestamp_ms: int) -> datetime:
    """
    Convert Unix timestamp in milliseconds to datetime.

    Args:
        timestamp_ms: Unix timestamp in milliseconds

    Returns:
        datetime object in UTC
    """
    return datetime.fromtimestamp(timestamp_ms / 1000.0, tz=timezone.utc)


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is timezone-aware in UTC.

    Args:
        dt: datetime object (naive or aware)

    Returns:
        Timezone-aware datetime in UTC
    """
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def get_time_range(start_dt: datetime, end_dt: datetime) -> str:
    """
    Get human-readable time range between two datetimes.

    Args:
        start_dt: Start datetime
        end_dt: End datetime

    Returns:
        Human-readable time range string
    """
    duration_ms = (end_dt - start_dt).total_seconds() * 1000
    return format_duration_ms(duration_ms)


def is_within_range(dt: datetime, start_dt: datetime, end_dt: datetime) -> bool:
    """
    Check if datetime is within a given range.

    Args:
        dt: datetime to check
        start_dt: Start of range
        end_dt: End of range

    Returns:
        True if dt is within range
    """
    return start_dt <= dt <= end_dt


def add_milliseconds(dt: datetime, ms: int) -> datetime:
    """
    Add milliseconds to datetime.

    Args:
        dt: datetime object
        ms: Milliseconds to add

    Returns:
        New datetime with milliseconds added
    """
    return dt + timedelta(milliseconds=ms)


def subtract_milliseconds(dt: datetime, ms: int) -> datetime:
    """
    Subtract milliseconds from datetime.

    Args:
        dt: datetime object
        ms: Milliseconds to subtract

    Returns:
        New datetime with milliseconds subtracted
    """
    return dt - timedelta(milliseconds=ms)


def get_simulation_time(start_time_ms: float, current_time_ms: float) -> float:
    """
    Get simulation time elapsed since start.

    Args:
        start_time_ms: Start time in milliseconds
        current_time_ms: Current time in milliseconds

    Returns:
        Elapsed simulation time in milliseconds
    """
    return current_time_ms - start_time_ms


def format_simulation_time(sim_time_ms: float) -> str:
    """
    Format simulation time for display.

    Args:
        sim_time_ms: Simulation time in milliseconds

    Returns:
        Formatted time string (e.g., "1.234s" or "45ms")
    """
    if sim_time_ms >= 1000:
        return f"{sim_time_ms / 1000:.3f}s"
    else:
        return f"{sim_time_ms:.0f}ms"


def parse_duration(duration_str: str) -> Optional[float]:
    """
    Parse duration string to milliseconds.

    Supports formats:
    - "1h 30m" -> 5400000 ms
    - "45s" -> 45000 ms
    - "500ms" -> 500 ms
    - "1.5s" -> 1500 ms

    Args:
        duration_str: Duration string

    Returns:
        Duration in milliseconds or None if parsing fails
    """
    if not duration_str:
        return None

    total_ms = 0.0

    # Pattern: number followed by unit (h, m, s, ms)
    pattern = r"(\d+\.?\d*)\s*(h|m|s|ms)"
    matches = re.findall(pattern, duration_str.lower())

    for value, unit in matches:
        num = float(value)
        if unit == "h":
            total_ms += num * 3600000
        elif unit == "m":
            total_ms += num * 60000
        elif unit == "s":
            total_ms += num * 1000
        elif unit == "ms":
            total_ms += num

    return total_ms if total_ms > 0 else None


def get_current_timestamp_ms() -> int:
    """
    Get current Unix timestamp in milliseconds.

    Returns:
        Current timestamp in milliseconds
    """
    return int(datetime.now(timezone.utc).timestamp() * 1000)


def timestamp_to_datetime_str(timestamp_ms: int) -> Optional[str]:
    """
    Convert timestamp milliseconds to ISO string.

    Args:
        timestamp_ms: Unix timestamp in milliseconds

    Returns:
        ISO formatted timestamp string or None if invalid
    """
    dt = from_timestamp_ms(timestamp_ms)
    if dt is None:
        return None  # type: ignore[unreachable]
    return format_timestamp(dt)
