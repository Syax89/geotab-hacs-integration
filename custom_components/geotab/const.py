"""Constants for the Geotab integration."""

DOMAIN = "geotab"
DEFAULT_SCAN_INTERVAL = 60

# Conversion factor from Pascals (Pa) to PSI
PA_TO_PSI = 0.000145038

# Define the diagnostics we want to fetch
DIAGNOSTICS_TO_FETCH = {
    "odometer": "DiagnosticOdometerAdjustmentId",
    "voltage": "DiagnosticGoDeviceVoltageId",
    "fuel_level": "DiagnosticFuelLevelId",
    "tire_pressure_front_left": "DiagnosticTirePressureFrontLeftId",
    "tire_pressure_front_right": "DiagnosticTirePressureFrontRightId",
    "tire_pressure_rear_left": "DiagnosticTirePressureRearLeftId",
    "tire_pressure_rear_right": "DiagnosticTirePressureRearRightId",
    "rpm": "DiagnosticEngineSpeedId",
    "coolant_temp": "DiagnosticEngineCoolantTemperatureId",
    "accelerator_pos": "DiagnosticAcceleratorPedalPositionId",
    "engine_hours": "DiagnosticEngineHoursAdjustmentId",
    "ignition": "DiagnosticIgnitionId",
    "door_status": "DiagnosticDoorAjarId",  # Common ID for any door being ajar
    "seatbelt_status": "DiagnosticDriverSeatbeltId",
}
