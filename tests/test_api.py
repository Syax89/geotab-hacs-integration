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
    assert data["device1"]["odometer"] == 100000


@pytest.mark.asyncio
async def test_api_get_data_empty_devices(mock_geotab_api):
    """Test that empty dict is returned when no devices exist."""
    mock_geotab_api.get.return_value = []
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
