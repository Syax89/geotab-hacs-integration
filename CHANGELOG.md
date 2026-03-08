# Changelog

All notable changes to this project are documented in this file.

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
- Mock `conftest.py` aligned with actual 23-diagnostic call_map (was missing `odometer_raw`, `engine_hours_raw`, `diagnostics_lookup`, and new ICE diagnostics)

## [1.2.2] - 2026-03-08

### Fixed
- **Last trip distance**: Trip query now uses `fromDate` (90 days ago) to fetch recent trips instead of oldest ones
- **Ignition state**: Use `isDriving=false` + `speed=0` as fallback when `isIgnitionOn` is absent, preventing stale ignition readings
- **Fault descriptions**: Resolve opaque diagnostic IDs via Geotab `Diagnostic` API for human-readable fault names
- **Engine hours**: Correctly derived from latest trip (~32.6h) instead of stale oldest trip (2.0h) — fixed by trip query improvement
- **RPM when parked**: Now correctly shows 0 when vehicle is off — fixed by ignition state improvement

## [1.2.1] - 2026-03-08

### Fixed
- Increased diagnostic `resultsLimit` multiplier from 2x to 10x per device to avoid missing data on large fleets

## [1.2.0] - 2026-02-20

### Changed
- **License**: Switched from Apache 2.0 to MIT License for maximum permissiveness
- **Dependencies**: Relaxed `mygeotab` from `==0.9.1` to `>=0.9.1,<1.0.0` for easier updates
- **Fault mappings**: Moved from hardcoded Italian strings to centralized `FAULT_DIAGNOSTIC_NAMES` dict in `const.py` (English, extensible)
- **Performance**: Blocking mygeotab calls consolidated into single `run_in_executor` (one thread, 45s timeout)

### Added
- **CI**: Matrix testing for Python 3.12 and 3.13
- **CI**: pip cache for faster dependency installation
- **CI**: Proper PYTHONPATH environment variable setup
- **Translations**: German (de), Spanish (es), French (fr), Portuguese (pt), Dutch (nl)
- **Sensors**: Per-sensor `suggested_display_precision` for better display formatting
- **Resilience**: Circuit breaker: after 5 consecutive API failures, updates pause for 300s
- **Authentication**: `InvalidAuth` now raises `ConfigEntryAuthFailed` for immediate re-auth prompt

### Fixed
- **CI**: Reliability improvements for pytest in GitHub Actions
- Manifest version sync (was stuck at 1.0.0)

### Documentation
- Comprehensive documentation update for v1.1.x series

## Previous Releases

## [1.1.8] - 2026-02-20

### Fixed
- Syntax error in `binary_sensor.py` preventing integration load (`unclosed f-string`)
- Improved fault diagnostic ID parsing with Italian translations

## [1.1.7] - 2026-02-19

### Fixed
- Trip distance unit correction (API returns km, not meters)
- Active Faults: added mapping for common diagnostic IDs to human-readable descriptions

### Changed
- Fault attributes now include `diagnostic_id` for debugging

## [1.1.6] - 2026-02-19

### Added
- Fallback mechanism for odometer and engine hours
- Last trip filtering to exclude zero-distance records
- Engine hours fallback from `Trip` data when diagnostics unavailable

### Fixed
- Ignition detection when `isIgnitionOn` is None (fallback to StatusData)

## [1.1.5] - 2026-02-19

### Changed
- Sort faults by `dateTime` descending (newest first)

## [1.1.4] - 2026-02-19

### Added
- Detailed fault attributes for `Active Faults` binary sensor:
  - `fault_count`
  - `faults_list` (formatted strings)
  - `faults_details` (structured data with code, timestamp, severity)

## [1.1.3] - 2026-02-19

### Fixed
- Engine hours showing "Unknown": switched to `DiagnosticEngineHoursAdjustmentId`
- Engine hours icon: removed conflicting `device_class`
- Last trip distance: improved sorting to show actual last trip

### Changed
- Odometer: switched to `DiagnosticOdometerAdjustmentId` for more reliable readings

## [1.1.2] - 2026-02-19

### Fixed
- Ignition accuracy: use `DeviceStatusInfo.isIgnitionOn` as authoritative source
- RPM: force to 0 when vehicle is not running

## [1.1.1] - 2026-02-19

### Fixed
- `KeyError` in `async_unload_entry` during config entry removal
- CI test stability in `test_config_flow.py`

## [1.1.0] - 2026-02-13

### Changed
- Robust device mapping and configuration cleanup

---

*Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/)*
