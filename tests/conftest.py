"""Global fixtures for Geotab integration tests."""
from unittest.mock import patch
import pytest

@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(request):
    """Enable custom integrations in Home Assistant."""
    if "hass" in request.fixturenames:
        hass = request.getfixturevalue("hass")
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

        # Prepare mock results for multi_call: status, diagnostics, faults, diagnostics_lookup, and 1 trip
        # Current api.py call_map order (v1.3.0, 23 diagnostics):
        # 1.  status
        # 2.  diag_odometer
        # 3.  diag_odometer_raw
        # 4.  diag_voltage
        # 5.  diag_fuel_level
        # 6.  diag_tire_pressure_front_left
        # 7.  diag_tire_pressure_front_right
        # 8.  diag_tire_pressure_rear_left
        # 9.  diag_tire_pressure_rear_right
        # 10. diag_rpm
        # 11. diag_coolant_temp
        # 12. diag_accelerator_pos
        # 13. diag_engine_hours
        # 14. diag_engine_hours_raw
        # 15. diag_ignition
        # 16. diag_door_status
        # 17. diag_seatbelt_status
        # 18. diag_oil_temp
        # 19. diag_oil_pressure
        # 20. diag_engine_load
        # 21. diag_transmission_temp
        # 22. diag_ambient_temp
        # 23. diag_fuel_rate
        # 24. diag_throttle_pos
        # 25. faults
        # 26. diagnostics_lookup
        # 27. trip_device1
        instance.multi_call.return_value = [
            # Status
            [{"device": {"id": "device1"}, "latitude": 45.0, "longitude": 9.0, "isDriving": True, "speed": 50.0}],
            # diag_odometer
            [{"device": {"id": "device1"}, "data": 100000, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_odometer_raw
            [{"device": {"id": "device1"}, "data": 100000, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_voltage
            [{"device": {"id": "device1"}, "data": 13.5, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_fuel_level
            [{"device": {"id": "device1"}, "data": 75.0, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_tire_pressure_front_left
            [{"device": {"id": "device1"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_tire_pressure_front_right
            [{"device": {"id": "device1"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_tire_pressure_rear_left
            [{"device": {"id": "device1"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_tire_pressure_rear_right
            [{"device": {"id": "device1"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_rpm
            [{"device": {"id": "device1"}, "data": 2500, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_coolant_temp
            [{"device": {"id": "device1"}, "data": 90, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_accelerator_pos
            [{"device": {"id": "device1"}, "data": 15, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_engine_hours
            [{"device": {"id": "device1"}, "data": 5000, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_engine_hours_raw
            [{"device": {"id": "device1"}, "data": 5000, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_ignition
            [{"device": {"id": "device1"}, "data": 1, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_door_status
            [{"device": {"id": "device1"}, "data": 0, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_seatbelt_status
            [{"device": {"id": "device1"}, "data": 0, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_oil_temp
            [{"device": {"id": "device1"}, "data": 95, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_oil_pressure
            [{"device": {"id": "device1"}, "data": 350000, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_engine_load
            [{"device": {"id": "device1"}, "data": 45, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_transmission_temp
            [{"device": {"id": "device1"}, "data": 80, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_ambient_temp
            [{"device": {"id": "device1"}, "data": 22, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_fuel_rate
            [{"device": {"id": "device1"}, "data": 8.5, "dateTime": "2026-03-08T10:00:00Z"}],
            # diag_throttle_pos
            [{"device": {"id": "device1"}, "data": 30, "dateTime": "2026-03-08T10:00:00Z"}],
            # Fault Data
            [{"device": {"id": "device1"}, "id": "fault1", "dateTime": "2026-02-13T12:00:00Z"}],
            # Diagnostics Lookup
            [{"id": "diag1", "name": "Test Diagnostic"}],
            # Trip Result for device1
            [
                {"id": "trip1", "distance": 15.0, "start": "2026-03-08T10:00:00Z", "stop": "2026-03-08T10:30:00Z", "maximumSpeed": 80, "drivingDuration": "PT25M", "idlingDuration": "PT5M"},
                {"id": "trip2", "distance": 22.5, "start": "2026-03-07T08:00:00Z", "stop": "2026-03-07T08:45:00Z", "maximumSpeed": 100, "drivingDuration": "PT40M", "idlingDuration": "PT3M"},
            ],
        ]
        yield instance
