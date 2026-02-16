# Changelog

All notable changes to Smart Battery Charging Controller will be documented in this file.

## [3.0.1] - 2024-02-16

### 🚀 Major Rewrite - Complete Architecture Overhaul

#### Added
- ✨ **Intelligent Peak Prediction** - Automatically detects price peaks 24-48 hours ahead
- 🎯 **4-Level Priority System** - Critical, High, Normal, Optional charging slots
- 📊 **Modern Dashboard** with Chart.js graphs (price forecast, SOC prediction)
- 🏗️ **Modular Architecture**:
  - `price_providers/` - OTE, Nanogreen, Nordpool, ENTSO-E support
  - `battery_controllers/` - GoodWe, Tesla, Huawei, Generic controllers
  - `charging_strategies/` - Intelligent optimization algorithms
- 🎨 **Beautiful UI/UX** - Gradient design, responsive layout, color-coded priorities
- 📱 **Real-time Monitoring** - Live SOC, price, and charging status
- ⚡ **Peak Preparation** - Ensures 80% SOC before price peaks
- 💰 **Opportunistic Full Charging** - Charges to 95% during ultra-cheap prices
- 🔒 **Safety Minimum** - Never drops below 20% SOC
- 📈 **SOC Prediction Chart** - 24-hour battery level forecast
- 🎛️ **Dashboard Controls** - Enable/disable auto-charging, force plan refresh

#### Changed
- 🧠 **Smarter Charging Logic**:
  - Peak detection algorithm (top 25% or >1.5x average)
  - Cheapest slot selection (bottom 35%)
  - Consecutive peak merging
  - 48-hour lookahead window
- 📦 **Better Code Organization**:
  - Abstract base classes for extensibility
  - Type hints throughout
  - Comprehensive docstrings
  - Error handling improvements

#### Technical
- Python 3.10+ required
- New dependencies: numpy, scikit-learn (for future ML)
- Chart.js 4.4.0 for graphs
- RESTful API endpoints for dashboard
- WebSocket-ready architecture

### Migration from v2.x

**Breaking Changes:**
- Configuration structure changed (use config flow for setup)
- Service names updated (backward compatible wrappers added)
- Sensor entity IDs may differ (check and update automations)

**Migration Steps:**
1. Backup your current configuration
2. Uninstall old version
3. Install v3.0.1 via HACS
4. Run config flow (Settings → Devices & Services)
5. Configure price provider and battery
6. Verify automations still work
7. Check dashboard at `/api/gw_smart_charging/dashboard`

### Known Issues
- Solar forecast integration not yet implemented (planned for 3.1.0)
- ML prediction model training in development (planned for 3.2.0)

---

## [2.4.0] - 2024-12

### Added
- Cost optimization sensor
- Enhanced sensor validation
- Price volatility detection

### Changed
- More aggressive optimization (5% threshold vs 10%)
- Extended 18-hour lookahead window

---

## [2.3.0] - 2024-11

### Added
- Improved dashboard with current configuration display
- Data status panel
- Enhanced test mode explanation
- Console debugging for graphs

### Changed
- Updated branding to Martin Rak
- Firmware version synced with tag

---

## [2.2.0] - 2024-11

### Added
- Multi-language support (Czech/English)
- Interactive Chart.js graphs
- 4 new charging strategies
- Full-hour charging cycles

---

## [2.1.0] - 2024-11

### Added
- 5 charging strategies
- 12-hour lookahead optimization

### Fixed
- Dashboard JSON parsing error
- Activation/deactivation buttons

---

## [2.0.0] - 2024-11

### Added
- Nanogreen integration
- Advanced ML patterns (workday/weekend/holiday)
- Switch control for additional devices
- Test mode
- Czech holiday detection

### Fixed
- Dashboard error 500 (missing aiohttp.web import)

---

For full release notes of previous versions, see individual `RELEASE_NOTES_*.md` files.

[3.0.1]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/3.0.1
[2.4.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/2.4.0
[2.3.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/2.3.0
[2.2.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/2.2.0
[2.1.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/2.1.0
[2.0.0]: https://github.com/someone11221/gw_smart_energy_charging/releases/tag/2.0.0
