#!/usr/bin/env python3
"""
DateTime utility functions for security scanner
"""

from datetime import datetime, timedelta


def get_timestamp_string() -> str:
    """
    Get current timestamp string for directory/file naming.

    Returns:
        Timestamp string in "YYYYMMDD_HHMMSS" format

    Examples:
        >>> # Returns something like '20251123_103045'
        >>> get_timestamp_string()
        '20251123_103045'
    """
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def convert_utc_to_jst(utc_datetime_str: str) -> str:
    """
    Convert UTC datetime string to JST format

    Args:
        utc_datetime_str: UTC datetime string (e.g., "2025-11-23T01:41:56.654958326Z")

    Returns:
        JST datetime string in "yyyy/MM/dd HH:mm:ss" format

    Examples:
        >>> convert_utc_to_jst("2025-11-23T01:41:56.654958326Z")
        '2025/11/23 10:41:56'
        >>> convert_utc_to_jst("2025-11-23T01:41:56Z")
        '2025/11/23 10:41:56'
    """
    # Replace Z with +00:00 for ISO format compatibility
    utc_datetime_str = utc_datetime_str.replace("Z", "+00:00")

    # Try to parse with fractional seconds
    try:
        dt_utc = datetime.fromisoformat(utc_datetime_str)
    except ValueError:
        # Fallback to basic format without fractional seconds
        dt_utc = datetime.fromisoformat(utc_datetime_str.split(".")[0] + "+00:00")

    # Convert to JST (UTC+9)
    dt_jst = dt_utc + timedelta(hours=9)

    # Format as "yyyy/MM/dd HH:mm:ss"
    return dt_jst.strftime("%Y/%m/%d %H:%M:%S")
