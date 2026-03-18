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

        # Prepare mock results for multi_call: status, faults, diagnostics lookup, and trips.
        # Order MUST match api.py _blocking_fetch_all.
        instance.multi_call.return_value = [
            # 0. Status
            [{
                "device": {"id": "device1"},
                "latitude": 45.0,
                "longitude": 9.0,
                "isDriving": True,
                "speed": 50.0,
                "dateTime": "2026-03-08T10:00:00Z",
                "statusData": [
                    {"diagnostic": {"id": "DiagnosticOdometerId"}, "data": 52015700, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticOdometerAdjustmentId"}, "data": 53203700, "dateTime": "9999-12-31T23:59:59Z"},
                    {"diagnostic": {"id": "DiagnosticTotalDistanceId"}, "data": 53203700, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticIgnitionId"}, "data": 1, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticEngineSpeedId"}, "data": 2500, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticFuelRateId"}, "data": 8.5, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticGoDeviceVoltageId"}, "data": 13.5, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticFuelLevelPercentageId"}, "data": 38.03, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticFuelLevelId"}, "data": 33.32, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticEngineHoursAdjustmentId"}, "data": 5000, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticEngineHoursId"}, "data": 5000, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticEngineLoadId"}, "data": 45, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticEngineCoolantTemperatureId"}, "data": 90, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticEngineOilTemperatureId"}, "data": 95, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticEngineOilPressureId"}, "data": 350000, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticAcceleratorPedalPositionId"}, "data": 15, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticThrottlePositionId"}, "data": 30, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticTransmissionOilTemperatureId"}, "data": 80, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticAmbientAirTemperatureId"}, "data": 22, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticTirePressureFrontLeftId"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticTirePressureFrontRightId"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticTirePressureRearLeftId"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticTirePressureRearRightId"}, "data": 220000, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticDoorAjarId"}, "data": 0, "dateTime": "2026-03-08T10:00:00Z"},
                    {"diagnostic": {"id": "DiagnosticDriverSeatbeltId"}, "data": 0, "dateTime": "2026-03-08T10:00:00Z"}
                ]
            }],
            # 1. Fault Data
            [{
                "device": {"id": "device1"},
                "id": "fault1",
                "dateTime": "2026-02-13T12:00:00Z",
                "diagnostic": {"id": "diag1"},
                "faultDescription": "Test fault"
            }],
            # 2. Diagnostics Lookup
            [{"id": "diag1", "name": "Test Diagnostic"}],
            # 3. Trip Result for device1
            [
                {"id": "trip1", "distance": 15.0, "start": "2026-03-08T10:00:00Z", "stop": "2026-03-08T10:30:00Z", "maximumSpeed": 80, "drivingDuration": "PT25M", "idlingDuration": "PT5M"},
                {"id": "trip2", "distance": 22.5, "start": "2026-03-07T08:00:00Z", "stop": "2026-03-07T08:45:00Z", "maximumSpeed": 100, "drivingDuration": "PT40M", "idlingDuration": "PT3M"},
            ],
        ]
        yield instance
