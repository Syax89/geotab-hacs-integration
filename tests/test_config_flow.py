"""Tests for Geotab config flow."""
from unittest.mock import patch, AsyncMock
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
    # Should not have a generic base error — only the field-level error
    assert "base" not in result["errors"]


@pytest.mark.asyncio
async def test_config_flow_boundary_scan_interval(hass):
    """Test that scan_interval=30 (boundary) is accepted."""
    with patch(
        "custom_components.geotab.config_flow.GeotabApiClient"
    ) as mock_client_cls, patch(
        "custom_components.geotab.async_setup_entry", return_value=True
    ):
        mock_client = mock_client_cls.return_value
        mock_client.async_authenticate = AsyncMock()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test@user.com",
                "password": "test-password",
                "database": "test-db",
                CONF_SCAN_INTERVAL: 30,
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY


@pytest.mark.asyncio
async def test_config_flow_success(hass):
    """Test a successful config flow."""
    with patch(
        "custom_components.geotab.config_flow.GeotabApiClient"
    ) as mock_client_cls, patch(
        "custom_components.geotab.async_setup_entry", return_value=True
    ):
        mock_client = mock_client_cls.return_value
        mock_client.async_authenticate = AsyncMock()

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test@user.com",
                "password": "test-password",
                "database": "test-db",
                CONF_SCAN_INTERVAL: 60,
            },
        )
        await hass.async_block_till_done()

        assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
        assert result["title"] == "test@user.com (test-db)"
        assert result["data"]["username"] == "test@user.com"
        assert result["data"]["database"] == "test-db"


@pytest.mark.asyncio
async def test_config_flow_invalid_auth(hass):
    """Test that invalid credentials show the correct error."""
    from custom_components.geotab.api import InvalidAuth

    with patch(
        "custom_components.geotab.config_flow.GeotabApiClient"
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.async_authenticate = AsyncMock(side_effect=InvalidAuth)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test@user.com",
                "password": "wrong-password",
                "database": "test-db",
                CONF_SCAN_INTERVAL: 60,
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_auth"


@pytest.mark.asyncio
async def test_config_flow_cannot_connect(hass):
    """Test that connection errors show the correct error."""
    from custom_components.geotab.api import ApiError

    with patch(
        "custom_components.geotab.config_flow.GeotabApiClient"
    ) as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.async_authenticate = AsyncMock(side_effect=ApiError)

        result = await hass.config_entries.flow.async_init(
            DOMAIN, context={"source": config_entries.SOURCE_USER}
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test@user.com",
                "password": "test-password",
                "database": "test-db",
                CONF_SCAN_INTERVAL: 60,
            },
        )

    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["base"] == "cannot_connect"


@pytest.mark.asyncio
async def test_options_flow(hass):
    """Test options flow."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="test@user.com",
        data={"username": "user", "password": "pass", "database": "db"},
        entry_id="test_id",
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
