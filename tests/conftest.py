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

        # Prepare mock results for multi_call: status, 25 diagnostics, faults, diagnostics_lookup, and trips
        # Order MUST match api.py _blocking_fetch_all and const.py DIAGNOSTICS_TO_FETCH
        instance.multi_call.return_value = [
            # 0. Status
            [{"device": {"id": "device1"}, "latitude": 45.0, "longitude": 9.0, "isDriving": True, "speed": 50.0, "dateTime": "2026-03-08T10:00:00Z"}],
            # 1. diag_odometer (AdjustmentId)
            [{"device": {"id": "device1"}, "data": 53203700, "dateTime": "9999-12-31T23:59:59Z"}],
            # 2. diag_odometer_raw (OdometerId)
            [{"device": {"id": "device1"}, "data": 52015700, "dateTime": "2026-03-08T10:00:00Z"}],
            # 3. diag_total_distance
            [{"device": {"id": "device1"}, "data": 53203700, "dateTime": "2026-03-08T10:00:00Z"}],
            # 4. diag_ignition
            [{"device": {"id": "device1"}, "data": 1, "dateTime": "2026-03-08T10:00:00Z"}],
            # 5. diag_voltage
            [{"device": {"id": "device1"}, "data": 13.5, "dateTime": "2026-03-08T10:00:00Z"}],
            # 6. diag_fuel_level (PercentageId)
            [{"device": {"id": "device1"}, "data": 38.03, "dateTime": "2026-03-08T10:00:00Z"}],
            # 7. diag_fuel_level_raw (FuelLevelId)
            [{"device": {"id": "device1"}, "data": 33.32, "dateTime": "2026-03-08T10:00:00Z"}],
            # 8. diag_fuel_rate
            [{"device": {"id": "device1"}, "data": 8.5, "dateTime": "2026-03-08T10:00:00Z"}],
            # 9. diag_rpm
            [{"device": {"id": "device1"}, "data": 2500, "dateTime": "2026-03-08T10:00:00Z"}],
            # 10. diag_engine_hours
            [{"device": {"id": "device1"}, "data": 5000, "dateTime": "2026-03-08T10:00:00Z"}],
            # 11. diag_engine_hours_raw
            [{"device": {"id": "device1"}, "data": 5000, "dateTime": "2026-03-08T10:00:00Z"}],
            # 12. diag_engine_load
            [{"device": {"id": "device1"}, "data": 45, "dateTime": "2026-03-08T10:00:00Z"}],
            # 13. diag_coolant_temp
            [{"device": {"id": "device1"}, "data": 90, "dateTime": "2026-03-08T10:00:00Z"}],
            # 14. diag_oil_temp
            [{"device": {"id": "device1"}, "data": 95, "dateTime": "2026-03-08T10:00:00Z"}],
            # 15. diag_oil_pressure
            [{"device": {"id": "device1"}, "data": 350000, "dateTime": "2026-03-08T10:00:00Z"}],
            # 16. diag_accelerator_pos
            [{"device": {"id": "device1"}, "data": 15, "dateTime": "2026-03-08T10:00:00Z"}],
            # 17. diag_throttle_pos
            [{"device": {"id": "device1"}, "data": 30, "dateTime": "2026-03-08T10:00:00Z"}],
            # 18. diag_transmission_temp
            [{"device": {"id": "device1"}, "data": 80, "dateTime": "2026-03-08T10:00:00Z"}],
            # 19. diag_ambient_temp
            [{"device": {"id": "device1"}, "data": 22, "dateTime": "2026-03-08T10:00:00Z"}],
            # 20. diag_tire_pressure_front_left
            [{"device": {"id": "device1"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"}],
            # 21. diag_tire_pressure_front_right
            [{"device": {"id": "device1"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"}],
            # 22. diag_tire_pressure_rear_left
            [{"device": {"id": "device1"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"}],
            # 23. diag_tire_pressure_rear_right
            [{"device": {"id": "device1"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"}],
            # 24. diag_door_status
            [{"device": {"id": "device1"}, "data": 0, "dateTime": "2026-03-08T10:00:00Z"}],
            # 25. diag_seatbelt_status
            [{"device": {"id": "device1"}, "data": 0, "dateTime": "2026-03-08T10:00:00Z"}],
            # 26. Fault Data
            [{"device": {"id": "device1"}, "id": "fault1", "dateTime": "2026-02-13T12:00:00Z"}],
            # 27. Diagnostics Lookup
            [{"id": "diag1", "name": "Test Diagnostic"}],
            # 28. Trip Result for device1
            [
                {"id": "trip1", "distance": 15.0, "start": "2026-03-08T10:00:00Z", "stop": "2026-03-08T10:30:00Z", "maximumSpeed": 80, "drivingDuration": "PT25M", "idlingDuration": "PT5M"},
                {"id": "trip2", "distance": 22.5, "start": "2026-03-07T08:00:00Z", "stop": "2026-03-07T08:45:00Z", "maximumSpeed": 100, "drivingDuration": "PT40M", "idlingDuration": "PT3M"},
            ],
        ]
        yield instance
