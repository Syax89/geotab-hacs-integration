"""Constants for the Geotab integration."""

DOMAIN = "geotab"
DEFAULT_SCAN_INTERVAL = 60
TRIP_FETCH_INTERVAL = 300  # Fetch trips every 5 minutes instead of every poll
AUTO_PRUNE_REPROBE_INTERVAL = 50  # Re-probe pruned diagnostics every 50 polls

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

# Define the diagnostics we want to fetch, grouped by category
DIAGNOSTICS_TO_FETCH = {
    # Driving & odometer
    "odometer": "DiagnosticOdometerAdjustmentId",
    "odometer_raw": "DiagnosticOdometerId",
    "ignition": "DiagnosticIgnitionId",
    # Energy & fuel
    "voltage": "DiagnosticGoDeviceVoltageId",
    "fuel_level": "DiagnosticFuelLevelPercentageId",
    "fuel_level_raw": "DiagnosticFuelLevelId",
    "fuel_rate": "DiagnosticFuelRateId",
    # Engine
    "rpm": "DiagnosticEngineSpeedId",
    "engine_hours": "DiagnosticEngineHoursAdjustmentId",
    "engine_hours_raw": "DiagnosticEngineHoursId",
    "engine_load": "DiagnosticEngineLoadId",
    "coolant_temp": "DiagnosticEngineCoolantTemperatureId",
    "oil_temp": "DiagnosticEngineOilTemperatureId",
    "oil_pressure": "DiagnosticEngineOilPressureId",
    # Pedals & throttle
    "accelerator_pos": "DiagnosticAcceleratorPedalPositionId",
    "throttle_pos": "DiagnosticThrottlePositionId",
    # Transmission & environment
    "transmission_temp": "DiagnosticTransmissionOilTemperatureId",
    "ambient_temp": "DiagnosticAmbientAirTemperatureId",
    # Tires
    "tire_pressure_front_left": "DiagnosticTirePressureFrontLeftId",
    "tire_pressure_front_right": "DiagnosticTirePressureFrontRightId",
    "tire_pressure_rear_left": "DiagnosticTirePressureRearLeftId",
    "tire_pressure_rear_right": "DiagnosticTirePressureRearRightId",
    # Safety & body
    "door_status": "DiagnosticDoorAjarId",
    "seatbelt_status": "DiagnosticDriverSeatbeltId",
}
