"""Tests for Geotab entities setup."""
import pytest
from unittest.mock import MagicMock
from custom_components.geotab.sensor import async_setup_entry as async_setup_sensor, SENSORS
from custom_components.geotab.binary_sensor import async_setup_entry as async_setup_binary, BINARY_SENSORS
from custom_components.geotab.device_tracker import async_setup_entry as async_setup_tracker
from custom_components.geotab.const import DOMAIN


def _make_coordinator(data=None):
    """Create a mock coordinator with optional data override."""
    coordinator = MagicMock()
    coordinator.data = data if data is not None else {
        "device1": {
            "id": "device1",
            "name": "Test Vehicle",
            "deviceType": "GO9",
            "latitude": 45.0,
            "longitude": 9.0,
            "isDriving": True,
            "speed": 50.0,
            "odometer": 100000,
            "ignition": 1,
            "last_trip": {
                "distance": 15000,
                "start": "2026-02-08T10:00:00Z",
                "stop": "2026-02-08T10:30:00Z",
            },
        }
    }
    coordinator.config_entry = MagicMock()
    coordinator.config_entry.data = {"database": "my.geotab.com"}
    return coordinator


def _make_entry():
    """Create a mock config entry."""
    entry = MagicMock()
    entry.entry_id = "test_id"
    entry.data = {"username": "user", "password": "pass", "database": "db"}
    entry.async_on_unload = MagicMock()
    return entry


@pytest.mark.asyncio
async def test_sensor_setup_creates_all_sensors(hass, mock_geotab_api):
    """Test that all sensor descriptions produce entities for each device."""
    entry = _make_entry()
    coordinator = _make_coordinator()
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_sensor(hass, entry, async_add_entities)

    assert async_add_entities.called
    entities = async_add_entities.call_args[0][0]
    # One entity per SENSORS description per device
    assert len(entities) == len(SENSORS)


@pytest.mark.asyncio
async def test_binary_sensor_setup_creates_all_sensors(hass, mock_geotab_api):
    """Test that all binary sensor descriptions produce entities for each device."""
    entry = _make_entry()
    coordinator = _make_coordinator()
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_binary(hass, entry, async_add_entities)

    assert async_add_entities.called
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == len(BINARY_SENSORS)


@pytest.mark.asyncio
async def test_device_tracker_setup(hass, mock_geotab_api):
    """Test that a device tracker entity is created per device."""
    entry = _make_entry()
    coordinator = _make_coordinator()
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_tracker(hass, entry, async_add_entities)

    assert async_add_entities.called
    entities = async_add_entities.call_args[0][0]
    assert len(entities) == 1


@pytest.mark.asyncio
async def test_sensor_setup_empty_coordinator(hass, mock_geotab_api):
    """Test sensor setup with no devices does not call async_add_entities."""
    entry = _make_entry()
    coordinator = _make_coordinator(data={})
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_sensor(hass, entry, async_add_entities)

    assert not async_add_entities.called


@pytest.mark.asyncio
async def test_sensor_setup_multiple_devices(hass, mock_geotab_api):
    """Test that entities are created for multiple devices."""
    entry = _make_entry()
    coordinator = _make_coordinator(
        data={
            "device1": {
                "id": "device1",
                "name": "Vehicle 1",
                "deviceType": "GO9",
                "isDriving": False,
                "odometer": 50000,
            },
            "device2": {
                "id": "device2",
                "name": "Vehicle 2",
                "deviceType": "GO8",
                "isDriving": True,
                "odometer": 120000,
            },
        }
    )
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    async_add_entities = MagicMock()
    await async_setup_sensor(hass, entry, async_add_entities)

    assert async_add_entities.called
    entities = async_add_entities.call_args[0][0]
    # All SENSORS descriptions × 2 devices
    assert len(entities) == len(SENSORS) * 2
