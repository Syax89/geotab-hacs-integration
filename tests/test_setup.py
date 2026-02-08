"""Tests for Geotab entities setup."""
import pytest
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
    
    # Binary sensors
    assert registry.async_get_entity_id("binary_sensor", DOMAIN, "device1_is_driving")

    # Clean shutdown
    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()
    await hass.async_stop()
