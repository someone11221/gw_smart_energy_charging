# Changelog

All notable changes to Smart Battery Charging Controller.

## [3.2.0] - 2026-02-18

### Added
- HDO signal reading from HA sensor (real-time NT/VT detection)
- Adaptive consumption prediction with exponential time decay weighting
- Fixed consumption prediction mode (manual kW values)
- Auto-detection of HA Energy Dashboard entities
- Lovelace custom card with automatic deployment to /config/www/
- Persistent cost statistics (today/week/month/year, survives HA restart)
- Debug logger with 500-event ring buffer
- Debug panel in dashboard with filtering and TXT/JSON download
- Emergency fallback charging mode (activates after 2h without price data)
- Config flow entity validation (checks sensor existence and data type)
- Configurable flat price for savings comparison
- Tooltips on all dashboard metric cards
- History chart with period selector (7d/30d/90d/year)
- Statistics tabs (today/week/month/year)
- Automatic cleanup of old entities from previous versions

### Changed
- Reduced to 7 sensors (costs and HDO merged into attributes)
- GoodWe controller always creates battery status (graceful fallback)
- All coordinator sections wrapped in try/except (no single crash kills update loop)
- Dashboard rewritten with improved SOC simulation (respects safety minimum)

### Fixed
- `is_nt_hour()` argument order (was crashing entire update loop)
- `get_monthly_fixed_charge()` missing distributor argument
- `TariffRate` field names (dist_vt/dist_nt, not vt_rate/nt_rate)
- `manifest.json` energy dependency removed (was preventing startup)
- StaticPathConfig crash on older HA versions
- SOC simulation dropping to 0% (now floors at safety minimum)

## [3.1.0] - 2026-02-18

### Added
- Price chart as hero dashboard element
- SOC prediction from backend data
- Cost tracking for current day

### Fixed
- UTC timezone bug in SOC chart
- Distribution rate parameter order

## [3.0.9] - 2026-02-17

### Added
- Czech distribution tariffs (EG.D, ČEZ, PRE)
- 15-minute scheduling intervals (96 slots/day)
- Consumption predictor from HA recorder
- HACS compatibility

## [3.0.8] - 2026-02-17

### Fixed
- Missing strings.json
- Translation inconsistencies
- Version mismatches across files
