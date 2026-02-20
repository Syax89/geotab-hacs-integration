"""Constants for the Geotab integration."""

DOMAIN = "geotab"
DEFAULT_SCAN_INTERVAL = 60

# Circuit breaker: open after this many consecutive API failures
CIRCUIT_BREAKER_MAX_FAILURES = 5
# Circuit breaker: seconds to wait before retrying after opening
CIRCUIT_BREAKER_RESET_DELAY = 300

# Mapping of diagnostic ID substrings to human-readable fault info (English)
FAULT_DIAGNOSTIC_NAMES: dict[str, dict[str, str]] = {
    "DeviceHasBeenUnplugged": {"name": "Device Unplugged", "code": "136"},
    "RestartedBecauseAllPower": {"name": "Device Restarted - Power Removed", "code": "130"},
    "LowVoltage": {"name": "Low Battery Voltage", "code": "131"},
    "FirmwareUpdate": {"name": "Firmware Update", "code": "132"},
    "InternalWatchdog": {"name": "Internal Watchdog", "code": "133"},
    "InternalReset": {"name": "Internal Reset", "code": "134"},
}

# Conversion factor from Pascals (Pa) to PSI
PA_TO_PSI = 0.000145038

# Define the diagnostics we want to fetch
DIAGNOSTICS_TO_FETCH = {
    "odometer": "DiagnosticOdometerAdjustmentId",
    "odometer_raw": "DiagnosticOdometerId",
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
    "engine_hours_raw": "DiagnosticEngineHoursId",
    "ignition": "DiagnosticIgnitionId",
    "door_status": "DiagnosticDoorAjarId",  # Common ID for any door being ajar
    "seatbelt_status": "DiagnosticDriverSeatbeltId",
}
