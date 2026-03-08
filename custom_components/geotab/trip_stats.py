"""Trip statistics aggregation functions for Geotab.

Pure functions with no Home Assistant dependencies.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone


def _parse_iso8601_duration(duration_str: str) -> float:
    """Parse an ISO 8601 duration string (e.g. PT5M30S) to total seconds.

    Supports: PnDTnHnMnS (days, hours, minutes, seconds).
    Returns 0.0 if the string cannot be parsed.
    """
    if not duration_str:
        return 0.0
    match = re.match(
        r"P(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+(?:\.\d+)?)S)?",
        duration_str,
    )
    if not match:
        return 0.0
    days = int(match.group(1) or 0)
    hours = int(match.group(2) or 0)
    minutes = int(match.group(3) or 0)
    seconds = float(match.group(4) or 0)
    return days * 86400 + hours * 3600 + minutes * 60 + seconds


def _parse_datetime(dt_str: str) -> datetime | None:
    """Parse an ISO datetime string to a timezone-aware datetime."""
    if not dt_str:
        return None
    try:
        dt = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except (ValueError, TypeError):
        return None


def _filter_trips_since(trips: list[dict], hours: int) -> list[dict]:
    """Return trips whose 'start' is within the last N hours."""
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    result = []
    for trip in trips:
        start = _parse_datetime(trip.get("start", ""))
        if start and start >= cutoff:
            result.append(trip)
    return result


def daily_distance(trips: list[dict]) -> float:
    """Total distance (km) of trips in the last 24 hours."""
    recent = _filter_trips_since(trips, 24)
    return round(sum(t.get("distance", 0) for t in recent), 2)


def weekly_distance(trips: list[dict]) -> float:
    """Total distance (km) of trips in the last 7 days."""
    recent = _filter_trips_since(trips, 7 * 24)
    return round(sum(t.get("distance", 0) for t in recent), 2)


def monthly_distance(trips: list[dict]) -> float:
    """Total distance (km) of trips in the last 30 days."""
    recent = _filter_trips_since(trips, 30 * 24)
    return round(sum(t.get("distance", 0) for t in recent), 2)


def daily_trip_count(trips: list[dict]) -> int:
    """Number of trips in the last 24 hours."""
    return len(_filter_trips_since(trips, 24))


def weekly_trip_count(trips: list[dict]) -> int:
    """Number of trips in the last 7 days."""
    return len(_filter_trips_since(trips, 7 * 24))


def average_trip_speed(trips: list[dict]) -> float | None:
    """Average of maximumSpeed across trips in the last 7 days (km/h)."""
    recent = _filter_trips_since(trips, 7 * 24)
    speeds = [t["maximumSpeed"] for t in recent if t.get("maximumSpeed") is not None]
    if not speeds:
        return None
    return round(sum(speeds) / len(speeds), 1)


def total_idle_time_weekly(trips: list[dict]) -> float | None:
    """Total idle time (hours) across trips in the last 7 days."""
    recent = _filter_trips_since(trips, 7 * 24)
    total_seconds = 0.0
    count = 0
    for trip in recent:
        idle = trip.get("idlingDuration")
        if idle is not None:
            total_seconds += _parse_iso8601_duration(str(idle))
            count += 1
    if count == 0:
        return None
    return round(total_seconds / 3600, 2)
