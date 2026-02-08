"""Tests for Geotab API client."""
import pytest
import aiohttp
from custom_components.geotab.api import GeotabApiClient, InvalidAuth, ApiError

@pytest.mark.asyncio
async def test_api_authenticate(mock_geotab_client):
    """Test API authentication."""
    async with aiohttp.ClientSession() as session:
        client = GeotabApiClient("user", "pass", "db", session)
        await client.async_authenticate()
        mock_geotab_client.authenticate.assert_called_once()

@pytest.mark.asyncio
async def test_api_get_data(mock_geotab_client):
    """Test API data retrieval."""
    async with aiohttp.ClientSession() as session:
        client = GeotabApiClient("user", "pass", "db", session)
        data = await client.async_get_full_device_data()
        
        assert "device1" in data
        assert data["device1"]["name"] == "Test Vehicle"
        assert data["device1"]["isDriving"] is True
        assert data["device1"]["odometer"] == 100000
