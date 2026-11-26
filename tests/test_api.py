"""Tests for Geotab API client."""
import asyncio
import socket
import pytest
from unittest.mock import MagicMock, patch
from mygeotab.exceptions import AuthenticationException

from custom_components.geotab.api import (
    GeotabApiClient,
    InvalidAuth,
    ApiError,
)


@pytest.mark.asyncio
async def test_api_authenticate(mock_geotab_api):
    """Test API authentication."""
    session = MagicMock()
    client = GeotabApiClient("user", "pass", "db", session)
    await client.async_authenticate()
    mock_geotab_api.authenticate.assert_called_once()


@pytest.mark.asyncio
async def test_api_authenticate_invalid_auth(mock_geotab_api):
    """Test that InvalidAuth is raised for bad credentials."""
    mock_geotab_api.authenticate.side_effect = AuthenticationException("user", "db", "server")
    session = MagicMock()
    client = GeotabApiClient("user", "wrong_pass", "db", session)
    with pytest.raises(InvalidAuth):
        await client.async_authenticate()


@pytest.mark.asyncio
async def test_api_authenticate_connection_error(mock_geotab_api):
    """Test that ApiError is raised for network errors."""
    mock_geotab_api.authenticate.side_effect = socket.gaierror
    session = MagicMock()
    client = GeotabApiClient("user", "pass", "db", session)
    with pytest.raises(ApiError):
        await client.async_authenticate()


@pytest.mark.asyncio
async def test_api_authenticate_timeout(mock_geotab_api):
    """Test that ApiError is raised on timeout."""
    mock_geotab_api.authenticate.side_effect = asyncio.TimeoutError
    session = MagicMock()
    client = GeotabApiClient("user", "pass", "db", session)
    with pytest.raises(ApiError):
        await client.async_authenticate()


@pytest.mark.asyncio
async def test_api_get_data(mock_geotab_api):
    """Test API data retrieval."""
    session = MagicMock()
    client = GeotabApiClient("user", "pass", "db", session)
    data = await client.async_get_full_device_data()

    assert "device1" in data
    assert data["device1"]["name"] == "Test Vehicle"
    assert data["device1"]["isDriving"] is True
    assert data["device1"]["odometer"] == 52015700


@pytest.mark.asyncio
async def test_api_get_data_empty_devices(mock_geotab_api):
    """Test that empty dict is returned when no devices exist."""
    mock_geotab_api.get.side_effect = lambda type_name, *args, **kwargs: [] if type_name == "Device" else []
    session = MagicMock()
    client = GeotabApiClient("user", "pass", "db", session)
    data = await client.async_get_full_device_data()
    assert data == {}


@pytest.mark.asyncio
async def test_api_get_data_api_error(mock_geotab_api):
    """Test that ApiError is raised on multi-call failure."""
    mock_geotab_api.multi_call.side_effect = Exception("API failure")
    session = MagicMock()
    client = GeotabApiClient("user", "pass", "db", session)
    with pytest.raises(ApiError):
        await client.async_get_full_device_data()


@pytest.mark.asyncio
async def test_api_get_data_invalid_auth(mock_geotab_api):
    """Expired/changed credentials during polling must raise InvalidAuth."""
    mock_geotab_api.get.side_effect = AuthenticationException("user", "db", "server")
    session = MagicMock()
    client = GeotabApiClient("user", "pass", "db", session)
    with pytest.raises(InvalidAuth):
        await client.async_get_full_device_data()


# ── Timeouts ────────────────────────────────────────────────────────────


def test_api_sets_request_timeout():
    """mygeotab must not use its 300s default request timeout."""
    from custom_components.geotab.api import REQUEST_TIMEOUT

    with patch("mygeotab.API") as mock_api:
        GeotabApiClient("user", "pass", "db", MagicMock())
    assert mock_api.call_args.kwargs["timeout"] == REQUEST_TIMEOUT


# ── Trip pagination ─────────────────────────────────────────────────────


def _trips(count, start, prefix="t"):
    from datetime import timedelta

    return [
        {
            "id": f"{prefix}{i}",
            "distance": 1.0,
            "start": start + timedelta(minutes=10 * i),
        }
        for i in range(count)
    ]


def test_complete_trips_fetches_newer_pages_when_truncated():
    """A full first page triggers a follow-up query from the newest trip."""
    from datetime import datetime, timedelta, timezone
    from custom_components.geotab.api import TRIP_RESULTS_LIMIT

    base = datetime(2026, 11, 1, tzinfo=timezone.utc)
    first = _trips(TRIP_RESULTS_LIMIT, base)
    newest_start = first[-1]["start"]
    # Second page repeats the boundary trip and adds 3 newer ones.
    second = [first[-1]] + _trips(3, newest_start + timedelta(minutes=10), "n")

    with patch("mygeotab.API") as mock_api:
        client = GeotabApiClient("user", "pass", "db", MagicMock())
        mock_api.return_value.get.return_value = second
        result = client._blocking_complete_trips("device1", first)

    mock_api.return_value.get.assert_called_once()
    search = mock_api.return_value.get.call_args.kwargs["search"]
    assert search["fromDate"] == newest_start
    assert search["deviceSearch"] == {"id": "device1"}
    assert len(result) == TRIP_RESULTS_LIMIT + 3
    assert len({trip["id"] for trip in result}) == len(result)


def test_complete_trips_no_extra_call_when_not_truncated():
    """A partial page is complete: no extra API call."""
    from datetime import datetime, timezone

    trips = _trips(5, datetime(2026, 11, 1, tzinfo=timezone.utc))
    with patch("mygeotab.API") as mock_api:
        client = GeotabApiClient("user", "pass", "db", MagicMock())
        result = client._blocking_complete_trips("device1", trips)

    mock_api.return_value.get.assert_not_called()
    assert result == trips


def test_complete_trips_stops_at_page_cap():
    """Pagination is bounded even if the API keeps returning full pages."""
    from datetime import datetime, timedelta, timezone
    from custom_components.geotab.api import TRIP_MAX_EXTRA_PAGES, TRIP_RESULTS_LIMIT

    base = datetime(2026, 1, 1, tzinfo=timezone.utc)
    pages = iter(
        _trips(TRIP_RESULTS_LIMIT, base + timedelta(days=10 * (n + 1)), f"p{n}_")
        for n in range(TRIP_MAX_EXTRA_PAGES + 5)
    )
    with patch("mygeotab.API") as mock_api:
        client = GeotabApiClient("user", "pass", "db", MagicMock())
        mock_api.return_value.get.side_effect = lambda *a, **k: next(pages)
        client._blocking_complete_trips("device1", _trips(TRIP_RESULTS_LIMIT, base))

    assert mock_api.return_value.get.call_count == TRIP_MAX_EXTRA_PAGES


# ── Ignition ────────────────────────────────────────────────────────────


def _ignition(status, diagnostics=None, timestamps=None, now=None):
    from datetime import datetime, timezone

    now = now or datetime(2026, 11, 26, 12, 0, tzinfo=timezone.utc)
    return GeotabApiClient._resolve_ignition(
        status, diagnostics or {}, timestamps or {}, now
    )


def _ago(minutes):
    from datetime import datetime, timedelta, timezone

    return datetime(2026, 11, 26, 12, 0, tzinfo=timezone.utc) - timedelta(minutes=minutes)


def test_ignition_on_while_driving():
    assert _ignition({"isDriving": True}, {"ignition": 0}, {"ignition": _ago(1)}) == 1


def test_ignition_stale_rpm_does_not_keep_ignition_on():
    """Last known RPM from hours ago must not override an 'off' ignition record."""
    assert (
        _ignition(
            {"isDriving": False, "speed": 0},
            {"rpm": 1500, "ignition": 0},
            {"rpm": _ago(180), "ignition": _ago(175)},
        )
        == 0
    )


def test_ignition_stale_rpm_without_ignition_record():
    assert (
        _ignition({"isDriving": False, "speed": 0}, {"rpm": 1500}, {"rpm": _ago(180)})
        == 0
    )


def test_ignition_fresh_rpm_newer_than_ignition_record():
    """Engine idling: fresh RPM reading after an old 'off' ignition record."""
    assert (
        _ignition(
            {"isDriving": False, "speed": 0},
            {"rpm": 800, "ignition": 0},
            {"rpm": _ago(1), "ignition": _ago(60)},
        )
        == 1
    )


def test_ignition_uses_ignition_diagnostic():
    assert _ignition({"isDriving": False}, {"ignition": 1}, {"ignition": _ago(30)}) == 1


def test_ignition_iso_string_timestamps():
    assert (
        _ignition(
            {"isDriving": False},
            {"rpm": 900},
            {"rpm": _ago(2).isoformat().replace("+00:00", "Z")},
        )
        == 1
    )


def test_ignition_unknown_without_signals():
    assert _ignition({}) is None


@pytest.mark.asyncio
async def test_api_get_data_ignition_end_to_end(mock_geotab_api):
    """Parked vehicle with an old RPM reading and ignition record 'off'."""
    status = mock_geotab_api.multi_call.return_value[0][0]
    status["isDriving"] = False
    status["speed"] = 0
    for item in status["statusData"]:
        if item["diagnostic"]["id"] == "DiagnosticIgnitionId":
            item["data"] = 0
            item["dateTime"] = "2026-03-08T10:05:00Z"

    client = GeotabApiClient("user", "pass", "db", MagicMock())
    data = await client.async_get_full_device_data()

    # Before: rpm > 0 forced ignition on regardless of age.
    assert data["device1"]["rpm"] == 2500
    assert data["device1"]["ignition"] == 0
