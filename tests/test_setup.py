"""Tests for Geotab entities setup."""
import pytest
from unittest.mock import patch, AsyncMock, MagicMock
from homeassistant.config_entries import ConfigEntryState
from homeassistant.helpers import entity_registry as er
from pytest_homeassistant_custom_component.common import MockConfigEntry
from custom_components.geotab.const import DOMAIN

@pytest.mark.asyncio
async def test_setup_entry_sets_up_platforms(hass, mock_geotab_api):
    """Test setting up the integration config entry and verify entities."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@user.com",
        data={"username": "user", "password": "pass", "database": "db"},
        entry_id="test_id"
    )
    entry.add_to_hass(hass)

    # Patch the coordinator to prevent real timers and background tasks
    mock_data = {
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
    
    with patch("custom_components.geotab.DataUpdateCoordinator") as mock_coord_class:
        coordinator = mock_coord_class.return_value
        coordinator.data = mock_data
        coordinator.async_config_entry_first_refresh = AsyncMock()
        coordinator.async_add_listener = MagicMock()
        coordinator.async_shutdown = MagicMock()
        
        # Trigger setup
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

        # Check that platforms are loaded
        assert entry.state == ConfigEntryState.LOADED
        
        # Verify entity registration
        registry = er.async_get(hass)
        
        # Device tracker (unique_id: device1_tracker)
        assert registry.async_get_entity_id("device_tracker", DOMAIN, "device1_tracker")
        
        # Basic Sensors
        assert registry.async_get_entity_id("sensor", DOMAIN, "device1_odometer")
        assert registry.async_get_entity_id("sensor", DOMAIN, "device1_speed")
        
        # Binary sensors
        assert registry.async_get_entity_id("binary_sensor", DOMAIN, "device1_is_driving")
        assert registry.async_get_entity_id("binary_sensor", DOMAIN, "device1_ignition")

    # Clean unload
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
