# 🗺️ Geotab HACS Integration - Software Roadmap

**Status:** v1.1.8 | **Last Updated:** February 2026

---

## ✅ Completed Features

* **Trip Sensor**: Implemented `last_trip_distance` with proper filter for zero-distance records.
* **Engine Hours**: Added fallback to raw diagnostic data when Adjustment ID is unavailable.
* **Ignition Detection**: Uses real-time `DeviceStatusInfo` with fallback to diagnostic history.
* **Active Faults Detail**: Full implementation with:
  * DTC code extraction
  * Human-readable Italian descriptions
  * Timestamp formatting
  * Severity indicators (lamp status)
* **Multi-language Support**: English and Italian translations.
* **CI/CD Pipeline**: GitHub Actions with hassfest validation and pytest.
* **HACS Integration**: Default badge and custom repository support.

---

## 🎯 Phase 1: Quality & Stability (v1.2.x)

*Objective: Stability improvements and async optimization.*

- [ ] **Unit Testing Expansion**: Increase code coverage beyond config flow and setup.
- [ ] **Async Wrapper**: Investigate non-blocking alternatives to `run_in_executor` for mygeotab API calls.
- [ ] **Error Recovery**: Improve handling of temporary API failures with exponential backoff.

---

## 🚀 Phase 2: New Features (v1.3.x)

*Objective: Expand data extraction and integrations.*

- [ ] **Multi-Account Support**: Manage multiple Geotab databases simultaneously.
- [ ] **Maintenance Reminders**: Sensor calculating days/km to next service based on Geotab rules.
- [ ] **Geofencing Sync**: Import MyGeotab zones as Home Assistant `zone` entities.
- [ ] **Trips History**: Sensor showing last trip duration, max speed, and idle time attributes.
- [ ] **Custom Parameters**: Support for reading GO device custom parameter data.

---

## 💎 Phase 3: User Experience (v1.4.x)

*Objective: Visual and ecosystem enhancements.*

- [ ] **Lovelace Card**: Custom card for vehicle telemetry display.
- [ ] **Services**: Implement HA services to force refresh or send messages to drivers.
- [ ] **Wiki Documentation**: Troubleshooting guide for common connectivity issues.
- [ ] **Energy Dashboard**: Integration with HA Energy for fuel tracking (where supported).

---

## 🛡️ Maintenance Notes

Priority remains **resilience** over features. Each v1.2+ feature must pass stability criteria before release: >95% uptime, graceful error handling, and minimal CPU/memory impact.

---

*Roadmap maintained by Aurora for Syax89.*
