"""Tests for Geotab config flow."""
from unittest.mock import patch
import pytest
from homeassistant import config_entries, data_entry_flow
from homeassistant.const import CONF_SCAN_INTERVAL
from custom_components.geotab.const import DOMAIN
from pytest_homeassistant_custom_component.common import MockConfigEntry

@pytest.mark.asyncio
async def test_config_flow_min_scan_interval(hass):
    """Test validation of minimum scan interval."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    
    # Simulate user input with interval < 30
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "username": "test@user.com",
            "password": "test-password",
            "database": "test-db",
            CONF_SCAN_INTERVAL: 10,
        },
    )
    
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"][CONF_SCAN_INTERVAL] == "min_scan_interval"

@pytest.mark.asyncio
async def test_options_flow(hass):
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@user.com",
        data={"username": "user", "password": "pass", "database": "db"},
        entry_id="test_id"
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.options.async_init(entry.entry_id)
    
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={CONF_SCAN_INTERVAL: 45},
    )

    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert entry.options == {CONF_SCAN_INTERVAL: 45}
