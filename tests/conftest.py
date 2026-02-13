"""Global fixtures for Geotab integration tests."""
from unittest.mock import patch
import pytest

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(hass):
    """Enable custom integrations in Home Assistant."""
    hass.data.pop("custom_components", None)
    yield

@pytest.fixture
def mock_geotab_api():
    """Mock the underlying mygeotab API library."""
    with patch("mygeotab.API") as mock:
        instance = mock.return_value
        instance.authenticate.return_value = True
        
        # Mock for .get("Device")
        instance.get.return_value = [{"id": "device1", "name": "Test Vehicle", "deviceType": "GO9"}]
        
        # Prepare mock results for multi_call: status, diagnostics, faults, and 1 trip
        # Current api.py logic for call_map:
        # 1. status
        # 2. diag_odometer
        # 3. diag_voltage
        # 4. diag_fuel_level
        # 5. diag_tire_pressure_front_left
        # 6. diag_tire_pressure_front_right
        # 7. diag_tire_pressure_rear_left
        # 8. diag_tire_pressure_rear_right
        # 9. diag_rpm
        # 10. diag_coolant_temp
        # 11. diag_accelerator_pos
        # 12. diag_engine_hours
        # 13. diag_ignition
        # 14. diag_door_status
        # 15. diag_seatbelt_status
        # 16. faults
        # 17. trip_device1
        instance.multi_call.return_value = [
            [{"device": {"id": "device1"}, "latitude": 45.0, "longitude": 9.0, "isDriving": True, "speed": 50.0}], # Status
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
            [{"device": {"id": "device1"}, "data": 5000}], # Engine Hours
            [{"device": {"id": "device1"}, "data": 1}], # Ignition
            [{"device": {"id": "device1"}, "data": 0}], # Door
            [{"device": {"id": "device1"}, "data": 0}], # Seatbelt
            # Fault Data
            [{"device": {"id": "device1"}, "id": "fault1", "dateTime": "2026-02-13T12:00:00Z"}],
            # Trip Result for device1
            [{"id": "trip1", "distance": 15000, "start": "2026-02-08T10:00:00Z", "stop": "2026-02-08T10:30:00Z"}] 
        ]
        yield instance
