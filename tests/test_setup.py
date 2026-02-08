"""Tests for Geotab entities setup."""
import pytest
from unittest.mock import MagicMock, AsyncMock
from custom_components.geotab.sensor import async_setup_entry as async_setup_sensor
from custom_components.geotab.binary_sensor import async_setup_entry as async_setup_binary
from custom_components.geotab.device_tracker import async_setup_entry as async_setup_tracker
from custom_components.geotab.const import DOMAIN

@pytest.mark.asyncio
async def test_platform_setup_entities(hass, mock_geotab_api):
    """Test individual platform setup directly to avoid HA core thread leaks."""
    entry = MagicMock()
    entry.entry_id = "test_id"
    entry.data = {"username": "user", "password": "pass", "database": "db"}
    
    # Mock coordinator
    coordinator = MagicMock()
    coordinator.data = {
        "device1": {
            "id": "device1", 
            "name": "Test Vehicle", 
            "deviceType": "GO9",
            "latitude": 45.0,
            "longitude": 9.0,
            "isDriving": True,
            "speed": 50.0,
            "odometer": 100000,
            "ignition": 1
        }
    }
    hass.data[DOMAIN] = {entry.entry_id: coordinator}

    # Setup callback mock
    async_add_entities = MagicMock()

    # Test Sensor setup
    await async_setup_sensor(hass, entry, async_add_entities)
    assert async_add_entities.called
    
    # Test Binary Sensor setup
    async_add_entities.reset_mock()
    await async_setup_binary(hass, entry, async_add_entities)
    assert async_add_entities.called

    # Test Device Tracker setup
    async_add_entities.reset_mock()
    await async_setup_tracker(hass, entry, async_add_entities)
    assert async_add_entities.called
