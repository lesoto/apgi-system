"""
Date and time utilities for consistent timestamp handling.

Provides timezone-aware datetime functions to avoid timezone comparison issues.
"""

from datetime import datetime, timezone
from typing import Union

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
    return dt.isoformat().replace('+00:00', 'Z')
