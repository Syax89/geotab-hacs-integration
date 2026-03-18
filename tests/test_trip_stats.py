"""Tests for trip_stats aggregation functions."""

from datetime import datetime, timedelta, timezone
import importlib.util
import os

import pytest

# Import trip_stats directly from file to avoid loading __init__.py (which needs homeassistant)
_TRIP_STATS_PATH = os.path.join(
    os.path.dirname(__file__),
    "..",
    "custom_components",
    "geotab",
    "trip_stats.py",
)
_spec = importlib.util.spec_from_file_location("trip_stats", _TRIP_STATS_PATH)
trip_stats = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(trip_stats)

_parse_iso8601_duration = trip_stats._parse_iso8601_duration
daily_distance = trip_stats.daily_distance
weekly_distance = trip_stats.weekly_distance
monthly_distance = trip_stats.monthly_distance
daily_trip_count = trip_stats.daily_trip_count
weekly_trip_count = trip_stats.weekly_trip_count
average_trip_speed = trip_stats.average_trip_speed
total_idle_time_weekly = trip_stats.total_idle_time_weekly


def _make_trip(
    distance: float = 10.0,
    hours_ago: float = 1.0,
    max_speed: float = 80.0,
    avg_speed: float = 60.0,
    idle_duration: str = "PT5M",
) -> dict:
    """Create a trip dict with a start time N hours ago."""
    start = datetime.now(timezone.utc) - timedelta(hours=hours_ago)
    return {
        "distance": distance,
        "start": start.isoformat(),
        "stop": (start + timedelta(minutes=30)).isoformat(),
        "maximumSpeed": max_speed,
        "averageSpeed": avg_speed,
        "idlingDuration": idle_duration,
    }


class TestParseISO8601Duration:
    """Tests for ISO 8601 duration parser."""

    def test_minutes_seconds(self):
        assert _parse_iso8601_duration("PT5M30S") == 330.0

    def test_hours_minutes(self):
        assert _parse_iso8601_duration("PT2H15M") == 8100.0

    def test_seconds_only(self):
        assert _parse_iso8601_duration("PT45S") == 45.0

    def test_days_hours(self):
        assert _parse_iso8601_duration("P1DT2H") == 93600.0

    def test_empty_string(self):
        assert _parse_iso8601_duration("") == 0.0

    def test_none(self):
        assert _parse_iso8601_duration(None) == 0.0

    def test_invalid(self):
        assert _parse_iso8601_duration("not-a-duration") == 0.0

    def test_fractional_seconds(self):
        assert _parse_iso8601_duration("PT1.5S") == 1.5


class TestDailyDistance:
    """Tests for daily_distance."""

    def test_trips_within_24h(self):
        trips = [_make_trip(10.0, 2), _make_trip(20.0, 5)]
        assert daily_distance(trips) == 30.0

    def test_excludes_old_trips(self):
        trips = [_make_trip(10.0, 2), _make_trip(20.0, 30)]
        assert daily_distance(trips) == 10.0

    def test_empty_trips(self):
        assert daily_distance([]) == 0.0


class TestWeeklyDistance:
    """Tests for weekly_distance."""

    def test_trips_within_7d(self):
        trips = [_make_trip(10.0, 24), _make_trip(20.0, 48)]
        assert weekly_distance(trips) == 30.0

    def test_excludes_old_trips(self):
        trips = [_make_trip(10.0, 24), _make_trip(20.0, 200)]
        assert weekly_distance(trips) == 10.0


class TestMonthlyDistance:
    """Tests for monthly_distance."""

    def test_trips_within_30d(self):
        trips = [_make_trip(10.0, 24), _make_trip(20.0, 24 * 20)]
        assert monthly_distance(trips) == 30.0


class TestTripCount:
    """Tests for trip count functions."""

    def test_daily_count(self):
        trips = [_make_trip(hours_ago=1), _make_trip(hours_ago=5), _make_trip(hours_ago=30)]
        assert daily_trip_count(trips) == 2

    def test_weekly_count(self):
        trips = [_make_trip(hours_ago=1), _make_trip(hours_ago=48), _make_trip(hours_ago=200)]
        assert weekly_trip_count(trips) == 2


class TestAverageTripSpeed:
    """Tests for average_trip_speed."""

    def test_average(self):
        trips = [
            _make_trip(max_speed=80, avg_speed=55, hours_ago=1),
            _make_trip(max_speed=120, avg_speed=85, hours_ago=24),
        ]
        assert average_trip_speed(trips) == 70.0

    def test_no_recent_trips(self):
        trips = [_make_trip(max_speed=80, hours_ago=200)]
        assert average_trip_speed(trips) is None

    def test_empty(self):
        assert average_trip_speed([]) is None


class TestTotalIdleTimeWeekly:
    """Tests for total_idle_time_weekly."""

    def test_with_idle_data(self):
        trips = [
            _make_trip(idle_duration="PT30M", hours_ago=1),
            _make_trip(idle_duration="PT1H", hours_ago=48),
        ]
        result = total_idle_time_weekly(trips)
        assert result == 1.5  # 0.5 + 1.0

    def test_no_idle_data(self):
        trips = [{"distance": 10, "start": _make_trip(hours_ago=1)["start"]}]
        assert total_idle_time_weekly(trips) is None

    def test_empty(self):
        assert total_idle_time_weekly([]) is None
