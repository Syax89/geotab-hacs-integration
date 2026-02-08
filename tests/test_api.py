"""Tests for Geotab API client."""
import pytest
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from custom_components.geotab.api import GeotabApiClient

@pytest.mark.asyncio
async def test_api_authenticate(hass, mock_geotab_client):
    """Test API authentication."""
    session = async_get_clientsession(hass)
    client = GeotabApiClient("user", "pass", "db", session)
    await client.async_authenticate()
    mock_geotab_client.authenticate.assert_called_once()

@pytest.mark.asyncio
async def test_api_get_data(hass, mock_geotab_client):
    """Test API data retrieval."""
    session = async_get_clientsession(hass)
    client = GeotabApiClient("user", "pass", "db", session)
    data = await client.async_get_full_device_data()
    
    assert "device1" in data
    assert data["device1"]["name"] == "Test Vehicle"
    assert data["device1"]["isDriving"] is True
    assert data["device1"]["odometer"] == 100000
