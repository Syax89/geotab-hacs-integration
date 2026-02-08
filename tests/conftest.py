"""Global fixtures for Geotab integration tests."""
from unittest.mock import patch
import pytest

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(hass):
    """Enable custom integrations in Home Assistant."""
    hass.data.pop("custom_components", None)
    yield

@pytest.fixture
def mock_geotab_client():
    """Mock Geotab API client."""
    with patch("custom_components.geotab.api.mygeotab.API") as mock:
        instance = mock.return_value
        instance.authenticate.return_value = True
        
        # Prepare mock results for devices, status and ALL diagnostics
        instance.multi_call.return_value = [
            [{"id": "device1", "name": "Test Vehicle", "deviceType": "GO9"}], # Devices
            [{"device": {"id": "device1"}, "latitude": 45.0, "longitude": 9.0, "isDriving": True}], # Status
            # Fill with mock data for every diagnostic we fetch
            [{"device": {"id": "device1"}, "data": 100000}], # Odometer
            [{"device": {"id": "device1"}, "data": 13.5}], # Voltage
            [{"device": {"id": "device1"}, "data": 75.0}], # Fuel
            [{"device": {"id": "device1"}, "data": 220000}], # Tire FL
            [{"device": {"id": "device1"}, "data": 220000}], # Tire FR
            [{"device": {"id": "device1"}, "data": 220000}], # Tire RL
            [{"device": {"id": "device1"}, "data": 220000}], # Tire RR
            [{"device": {"id": "device1"}, "data": 2500}], # RPM
            [{"device": {"id": "device1"}, "data": 90}], # Coolant
            [{"device": {"id": "device1"}, "data": 15}], # Accelerator
            [{"device": {"id": "device1"}, "data": 0}], # Door
            [{"device": {"id": "device1"}, "data": 0}], # Seatbelt
        ]
        yield instance
