"""Time utility functions."""

from datetime import datetime
import pytz


def get_sofia_time() -> datetime:
    """
    Get current time in Sofia timezone (Europe/Sofia).

    Returns:
        Current datetime in Sofia timezone
    """
    sofia_tz = pytz.timezone("Europe/Sofia")
    return datetime.now(sofia_tz)


def format_datetime(dt: datetime, format_str: str = "%Y-%m-%d %H:%M:%S %Z") -> str:
    """
    Format datetime to string.

    Args:
        dt: Datetime object to format
        format_str: Format string

    Returns:
        Formatted datetime string
    """
    return dt.strftime(format_str)
