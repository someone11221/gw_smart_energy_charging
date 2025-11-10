# Changelog

All notable changes to GW Smart Energy Charging will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.3.0] - 2024-11-10

### 🔄 MAJOR UPDATE - Hourly Charging Logic

**Breaking Changes:**
- **Converted from 15-minute to hourly charging intervals** - The system now operates on hourly charging cycles instead of 15-minute intervals for better battery health and stability
- All input sensors are automatically aggregated to hourly values
- Schedules now show 24 hourly slots instead of 96 15-minute slots

### ✨ Added

**Dashboard Improvements:**
- **Fixed battery SOC forecast display** - Now properly shows battery state predictions for next 24 hours
- **Current charging logic indicator** - Dashboard now displays which charging strategy is active
- **Planned charging visualization** - Clear display of when battery will charge/discharge
- **Enhanced test mode controls** - Better hints and explanations for testing different parameters
- **More configuration parameters visible** - Extended dashboard to show all key settings
- **Robust testing environment** - New testing panel with parameter presets and simulation modes

**Configuration Enhancements:**
- **Prettier configuration flow** - Redesigned UI with better organization and visual hierarchy
- **Helpful hints and tooltips** - Every configuration option now has explanatory text
- **Parameter validation** - Real-time validation with helpful error messages
- **Configuration templates** - Pre-configured templates for common scenarios

**Code Quality:**
- **Comprehensive code comments** - All major functions and logic paths now documented
- **Reduced complexity** - Removed redundant entities and simplified data flow
- **Better error handling** - More robust error messages and recovery mechanisms
- **Performance optimizations** - Reduced update frequency and improved data caching

### 🔧 Changed

**Version & Branding:**
- Updated version to 2.3.0 in manifest.json
- Changed manufacturer from "GW Energy Solutions" to "Martin Rak"
- Firmware version now matches release tag (2.3.0)

**Dashboard Updates:**
- Version footer updated to 2.3.0
- Improved graph rendering for hourly data
- Better responsive design for mobile devices
- Enhanced color coding for different charging modes

**Logic Improvements:**
- Hourly state calculations instead of 15-minute intervals
- Simplified decision tree for charging operations
- Better integration with Nanogreen hourly pricing
- Improved solar forecast aggregation

### 🐛 Fixed

- **Battery forecast not showing in dashboard** - Resolved data binding issues
- **Graph display errors** - Fixed rendering of forecast and charging states
- **Test mode toggle functionality** - Now properly enables/disables test mode
- **Configuration validation** - Better handling of edge cases and invalid inputs

### 📚 Documentation

- **CHANGELOG.md** - This file, shown during HACS updates
- **Updated README.md** - Reflects new hourly logic and v2.3.0 features
- **Inline code comments** - Extensive documentation in all Python files
- **Configuration guide** - New section explaining all parameters with examples

### 🗑️ Removed

- **Unnecessary 15-minute interval sensors** - Consolidated to hourly data
- **Redundant forecast entities** - Merged into main forecast sensor
- **Deprecated configuration options** - Cleaned up legacy settings

### 🎯 Suggested Improvements (Implemented)

1. **Smart battery wear reduction** - Hourly cycles reduce battery switching
2. **Better price optimization** - Hourly blocks allow better planning
3. **Simplified user interface** - Fewer entities, clearer purpose
4. **Testing framework** - Built-in scenarios for validation
5. **Configuration presets** - Quick setup for common use cases

### 📦 Migration from v2.2.0

**Automatic Migration:**
- No manual steps required
- Existing configurations automatically converted to hourly logic
- Sensor states preserved with new hourly aggregation
- Historical data remains accessible

**What to Expect:**
- Charging/discharging will happen in full hour blocks
- Dashboard graphs show 24 hourly bars instead of 96 15-minute points
- More stable battery operation with fewer mode switches
- Slightly less granular control but better for battery health

**Recommended Actions:**
1. Review your charging strategy in configuration
2. Check critical hours settings (now aligned to hour boundaries)
3. Verify additional switches still work as expected
4. Monitor first 24 hours to ensure expected behavior

### ⚠️ Known Issues

- None currently identified

### 🔮 Coming in v2.4.0

- Advanced battery health monitoring
- Machine learning improvements for hourly patterns
- Integration with more pricing providers
- Extended holiday calendar support
- Mobile app for remote monitoring

---

## [2.2.0] - 2024-11-08

### Added
- Multi-language support (Czech and English)
- Interactive Chart.js graphs (Price, SOC forecast, Solar production)
- 4 new charging strategies (Adaptive, Solar Priority, Peak Shaving, TOU)
- Full hour charging cycles option
- Extended configuration options

### Changed
- Dashboard version to 2.2.0
- Improved graph rendering and interactivity

---

## [2.1.0] - 2024-11-06

### Fixed
- Dashboard 24-hour prediction JSON parsing error
- Activation/Deactivation button functionality

### Added
- 5 configurable charging strategies
- 12-hour lookahead for better price optimization

### Changed
- Improved strategy selection logic
- Better logging for debugging

---

## [2.0.0] - 2024-11-04

### Added
- Nanogreen integration support
- Advanced ML patterns (weekday/weekend/holiday)
- Additional switches with price control
- Test mode for safe debugging
- Czech holiday detection

### Fixed
- Dashboard Error 500 (missing aiohttp.web import)

---

## [1.9.5] - 2024-11-02

### Added
- Optimal charging timing (waits for cheapest hour)
- Control panel in dashboard
- 24-hour prediction timeline

### Changed
- Improved price trend detection (10% threshold)

---

## [1.9.0] - 2024-10-30

### Added
- Custom Lovelace card
- Panel in Home Assistant sidebar
- Options Flow for reconfiguration
- Energy Dashboard integration support

---

## [1.8.0] - 2024-10-28

### Added
- Device Panel integration
- Entity consolidation (21 → 10 entities)

### Fixed
- Diagnostics sensor now shows current SOC correctly

### Documentation
- Added CHARGING_LOGIC.md

---

For older versions, see individual release notes files in the repository root.

[2.3.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/v2.3.0
[2.2.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/v2.2.0
[2.1.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/v2.1.0
[2.0.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/v2.0.0
[1.9.5]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/v1.9.5
[1.9.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/v1.9.0
[1.8.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/v1.8.0
