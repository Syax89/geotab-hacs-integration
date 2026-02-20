# Changelog

All notable changes to this project are documented in this file.

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
