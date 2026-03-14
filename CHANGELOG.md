# Changelog

All notable changes to this project are documented in this file.

## [1.4.8] - 2026-03-14

### Fixed
- **Tire Pressure Sensors**: Fixed all four tire pressure sensors showing `0 PSI` instead of "unavailable" when no data is present from the vehicle.
- **Circuit Breaker Recovery**: Fixed the circuit breaker not resetting its failure counter after the cooldown period, which caused it to re-open immediately on the first subsequent error.
- **Entity Stability**: Fixed a `KeyError` crash that occurred when a vehicle was removed from the Geotab fleet while the integration was running. Entities now gracefully become "unavailable".
- **Code Cleanup**: Removed unused `DeviceInfo` import from `device_tracker.py`.

## [1.4.7] - 2026-03-08

### Fixed
- **Ignition Sensing**: Improved real-time ignition detection by prioritizing engine RPM (>0). This ensures the vehicle shows as "On" immediately when engine activity is detected, even if the primary API ignition flag is delayed.

## [1.4.6] - 2026-03-08

### Fixed
- **Hotfix**: Resolved a `SyntaxError` in `api.py` introduced in the previous version that prevented the integration from loading correctly.

## [1.4.5] - 2026-03-08

### Fixed
- **System Stability**: Moved the `mygeotab` library import inside methods to prevent blocking calls during integration loading, satisfying Home Assistant's strict asynchronous requirements.

## [1.4.4] - 2026-03-08

### Fixed
- **CI Stability**: Synchronized test fixtures (`conftest.py`) with the new sensor count and diagnostic ordering to restore passing test states.

## [1.4.3] - 2026-03-08

### Fixed
- **Odometer Precision**: Enhanced logic to correctly capture and prioritize future-dated `OdometerAdjustment` values (year 9999), which Geotab uses to store the current officially calibrated odometer reading.

## [1.4.2] - 2026-03-08

### Fixed
- **Fuel & Odometer Accuracy**: Switched primary Odometer to `DiagnosticOdometerId` and refined Fuel Level logic based on live vehicle data (Opel Corsa) to ensure parity with the MyGeotab portal.

### Added
- **Odometer (Adjustment)**: Added a new diagnostic sensor for the manually calibrated odometer offset.

## [1.4.1] - 2026-03-08

### Fixed
- **Odometer Accuracy**: Improved fallback logic for the primary Odometer sensor. It now prioritizes `OdometerAdjustment`, then falls back to `Odometer` (Raw ECU), and finally `TotalDistance`.

### Added
- **Odometer Diagnostics**: Added `odometer_raw` and `total_distance` sensors (disabled by default) to help users identify the correct odometer source for their specific vehicle.

## [1.4.0] - 2026-03-08

### Changed
- **Fuel Level**: Switched primary Fuel Level sensor to use `DiagnosticFuelLevelPercentageId`, which provides a more consistent 0-100% value across different vehicle types.

### Added
- **Fuel Level (Raw)**: Added a new diagnostic sensor `fuel_level_raw` (disabled by default) that reports the original `DiagnosticFuelLevelId` value for troubleshooting and specific vehicle configurations.

## [1.3.9] - 2026-03-08

### Fixed
- **Localization**: Switched to `translation_key` for all entities to ensure names are correctly localized according to the Home Assistant language settings (fixes issues where names appeared in English on Italian systems).

## [1.3.8] - 2026-03-08

### Fixed
- **Hassfest Validation**: Corrected invalid translation keys (renamed `dateTime` to `last_update`) to comply with Home Assistant standards (lowercase only).

## [1.3.7] - 2026-03-08

### Fixed
- **API Robustness**: Improved the data processing loop to prevent potential index errors during multi-call handling.
- **Data Integrity**: Strictly enforced boolean returns for the Driving status binary sensor.
- **Repository Metadata**: Corrected repository URLs and manifest versioning for better synchronization with GitHub.
- **Code Quality**: Cleaned up unused imports and refined internal logic.

## [1.3.6] - 2026-03-08

### Fixed
- **Stability**: Refined `dateTime` sensor logic for improved data handling and robustness.
- **Test Suite**: Updated test mocks and coordinator data to ensure consistent test coverage across different environments.

## [1.3.4] - 2026-03-08

### Changed
- **Improved Icons**: Updated the icon for Accelerator Position to `mdi:car-speed-limiter` and Throttle Position to `mdi:circle-slice-8` for better visual clarity and distinction.

## [1.3.3] - 2026-03-08

### Added
- **Full Localization Support**: Updated all supported languages (DE, ES, FR, NL, PT) with the new localized entity name structure and UI organization.

## [1.3.2] - 2026-03-08

### Added
- **Localized Entity Names**: Added support for translated entity names in English and Italian.
- **Improved UI Organization**: Grouped sensors using prefixes (e.g., "Motore:", "Viaggi:", "Pneumatici:") in the Italian translation for better clarity in the Home Assistant UI.

## [1.3.1] - 2026-03-08

### Changed
- **Reorganized Sensors**: Grouped sensors into logical categories (Primary, Performance, Engine Health, Environmental, Trip Stats, System) for better UI clarity.
- **Reorganized Binary Sensors**: Grouped binary sensors into logical categories (Operation, Health, Safety).
- **Entity Categories**: Improved use of `EntityCategory.DIAGNOSTIC` for technical sensors.

## [1.3.0] - 2026-03-08

### Added
- **Trip Statistics**: 7 new sensors (disabled by default): Daily/Weekly/Monthly Distance, Daily/Weekly Trip Count, Avg Trip Speed (7d), Weekly Idle Time
- **ICE Diagnostics**: 7 new sensors (disabled by default): Oil Temperature, Oil Pressure, Engine Load, Transmission Temperature, Ambient Temperature, Fuel Rate, Throttle Position
- **Trip History**: Expanded trip fetch from 10 to 200 results, stored as `trip_history` for aggregation
- **Service `geotab.refresh`**: Force immediate data refresh from Developer Tools
- **Auto-pruning**: Diagnostics returning empty data for all devices are automatically skipped; re-probed every 50 polls
- **Trip fetch interval**: Trips fetched every 5 minutes instead of every poll (saves API calls)
- **Structured logging**: Device-name prefixed logs, summary counts per update

### Changed
- Total entities per device: 35 (29 sensors + 5 binary sensors + 1 device tracker); 14 new sensors disabled by default

### Fixed
- Mock `conftest.py` aligned with actual 23-diagnostic call_map

## Previous Releases ... (rest of file)
