"""Trip statistics aggregation functions for Geotab.

Pure functions with no Home Assistant dependencies.
"""

from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

# .NET TimeSpan format used by the Geotab API: [-][d.]hh:mm:ss[.fffffff]
_TIMESPAN_RE = re.compile(
    r"^(?:(\d+)\.)?(\d{1,2}):(\d{1,2}):(\d{1,2}(?:\.\d+)?)$"
)


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


def _parse_duration(value: Any) -> float:
    """Parse a Geotab duration to total seconds.

    The Geotab API returns durations as .NET TimeSpan strings
    (e.g. "00:05:30" or "1.02:03:04.5000000"). ISO 8601 strings, timedelta
    objects and plain numbers (seconds) are accepted as well.
    Returns 0.0 if the value cannot be parsed.
    """
    if value is None or isinstance(value, bool):
        return 0.0
    if isinstance(value, timedelta):
        return value.total_seconds()
    if isinstance(value, (int, float)):
        return float(value)
    text = str(value).strip()
    if not text:
        return 0.0
    if match := _TIMESPAN_RE.match(text):
        days = int(match.group(1) or 0)
        return (
            days * 86400
            + int(match.group(2)) * 3600
            + int(match.group(3)) * 60
            + float(match.group(4))
        )
    if text.startswith("P"):
        return _parse_iso8601_duration(text)
    return 0.0


def _parse_datetime(value: Any) -> datetime | None:
    """Parse a datetime (object or ISO string) to a timezone-aware datetime.

    The mygeotab library already deserializes date fields to datetime
    objects, so both forms must be supported.
    """
    if isinstance(value, datetime):
        if value.tzinfo is None:
            return value.replace(tzinfo=timezone.utc)
        return value
    if not value or not isinstance(value, str):
        return None
    try:
        dt = datetime.fromisoformat(value.replace("Z", "+00:00"))
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
        start = _parse_datetime(trip.get("start"))
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
    """Average driving speed across trips in the last 7 days (km/h)."""
    recent = _filter_trips_since(trips, 7 * 24)
    speeds = [t["averageSpeed"] for t in recent if t.get("averageSpeed") is not None]
    if not speeds:
        return None
    return round(sum(speeds) / len(speeds), 1)


def last_trip_average_speed(trip: dict | None) -> float | None:
    """Return the average speed of the most recent trip (km/h)."""
    if not trip:
        return None
    average_speed = trip.get("averageSpeed")
    if average_speed is None:
        return None
    return round(float(average_speed), 1)


def last_trip_duration_hours(trip: dict | None) -> float | None:
    """Return the total duration of the most recent trip in hours."""
    if not trip:
        return None

    driving_seconds = _parse_duration(trip.get("drivingDuration"))
    idle_seconds = _parse_duration(trip.get("idlingDuration"))
    total_seconds = driving_seconds + idle_seconds

    if total_seconds == 0:
        start = _parse_datetime(trip.get("start"))
        stop = _parse_datetime(trip.get("stop"))
        if start and stop and stop >= start:
            total_seconds = (stop - start).total_seconds()

    if total_seconds == 0:
        return None
    return round(total_seconds / 3600, 2)


def total_idle_time_weekly(trips: list[dict]) -> float | None:
    """Total idle time (hours) across trips in the last 7 days."""
    recent = _filter_trips_since(trips, 7 * 24)
    total_seconds = 0.0
    count = 0
    for trip in recent:
        idle = trip.get("idlingDuration")
        if idle is not None:
            total_seconds += _parse_duration(idle)
            count += 1
    if count == 0:
        return None
    return round(total_seconds / 3600, 2)
