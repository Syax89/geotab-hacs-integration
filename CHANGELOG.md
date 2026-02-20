# Changelog

All notable changes to this project are documented in this file.

## [1.1.9] - 2026-02-20

### Added
- Per-sensor `suggested_display_precision` so HA displays the right number of
  decimal places without discarding precision in the stored value
- Circuit breaker: after 5 consecutive API failures updates pause for 300 s
  before retrying, preventing hammering an unavailable API
- `InvalidAuth` now raises `ConfigEntryAuthFailed` so HA immediately prompts
  re-authentication instead of silently retrying

### Changed
- Fault diagnostic name mappings moved from hardcoded Italian strings in
  `binary_sensor.py` to a centralized `FAULT_DIAGNOSTIC_NAMES` dict in
  `const.py` (English, easy to extend)
- All blocking mygeotab calls consolidated into a single `run_in_executor`
  call per coordinator update (one thread instead of two, one 45 s timeout)
- `mygeotab` dependency relaxed from `==0.9.1` to `>=0.9.1,<1.0.0` to allow
  patch/minor updates without requiring a manual manifest bump

### Fixed
- Manifest version was stuck at `1.0.0` despite code being at `1.1.8`

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
