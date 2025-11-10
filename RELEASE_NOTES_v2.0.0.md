# GW Smart Charging v2.0.0 Release Notes

**Release Date:** November 2024  
**Major Version Update**

---

## 🎉 What's New in v2.0.0

Version 2.0.0 is a major update that brings advanced features, improved machine learning, and better integration with Home Assistant ecosystem.

### 🔋 Nanogreen Sensor Integration

**NEW:** Support for Nanogreen cheapest hours sensor (`sensor.is_currently_in_five_cheapest_hours`)

- Automatically charges battery during the 5 cheapest hours detected by Nanogreen
- Falls back to standard logic when sensor is unavailable
- Seamless integration without breaking existing configurations
- Configurable through UI

**Benefits:**
- Maximize savings by charging during absolute cheapest periods
- No manual intervention required
- Works alongside existing price threshold logic

**Configuration:**
```yaml
Nanogreen Cheapest Sensor: sensor.is_currently_in_five_cheapest_hours
```

---

### 🧠 Advanced Machine Learning Patterns

**ENHANCED:** Separate ML models for weekdays, weekends, and holidays

- **Weekday Patterns** - Learn typical Monday-Friday consumption
- **Weekend Patterns** - Separate model for Saturday-Sunday behavior
- **Holiday Patterns** - Special patterns for Czech public holidays
- **Automatic Holiday Detection** - Recognizes major Czech holidays

**Supported Holidays:**
- New Year's Day (1/1)
- Labour Day (1/5)
- Victory Day (8/5)
- Saints Cyril and Methodius (5/7)
- Jan Hus Day (6/7)
- Czech Statehood Day (28/9)
- Independent Czechoslovak State Day (28/10)
- Struggle for Freedom and Democracy Day (17/11)
- Christmas Eve (24/12)
- Christmas Day (25/12)
- St. Stephen's Day (26/12)

**Benefits:**
- More accurate consumption predictions
- Better charging schedule optimization
- Adapts to different lifestyle patterns
- Maintains 30-day history for each pattern type

---

### 🔌 Additional Switches Management

**NEW:** Control any Home Assistant switches based on electricity prices

- Add multiple switches via configuration (comma-separated)
- Switches turn ON when price drops below threshold
- Switches turn OFF when price rises above threshold
- Perfect for:
  - Water heaters
  - Pool pumps
  - EV chargers
  - Dishwashers
  - Washing machines
  - Any high-consumption devices

**Configuration Example:**
```yaml
Additional Switches: switch.water_heater,switch.pool_pump,switch.ev_charger
Switch Price Threshold: 2.0  # CZK/kWh
```

**Features:**
- Independent state tracking for each switch
- Automatic control based on real-time prices
- Configurable price threshold
- Works with test mode
- Detailed logging for debugging

**Use Case:**
```
Price drops to 1.5 CZK/kWh → Turn ON water heater, pool pump
Price rises to 2.5 CZK/kWh → Turn OFF water heater, pool pump
```

---

### 🧪 Advanced Testing & Debugging Mode

**NEW:** Test mode for safe testing and debugging

- Enable via configuration UI
- Prevents actual charging/discharging commands
- Logs all actions that would be taken
- Perfect for:
  - Testing new configurations
  - Debugging issues
  - Understanding integration behavior
  - Safe experimentation

**Test Mode Features:**
- No actual script execution
- No switch state changes
- Full logging of intended actions
- All sensors continue updating
- Schedule computation still runs

**Enable Test Mode:**
```yaml
Test Mode: true
```

**Example Log Output:**
```
TEST MODE: Would turn ON charging (slot 45, mode: grid_charge, price: 1.50 CZK/kWh)
TEST MODE: Would turn ON switch switch.water_heater (price: 1.50 CZK/kWh)
```

---

### 🐛 Bug Fixes

#### Dashboard Error 500 - FIXED ✅

**Issue:** Dashboard was throwing HTTP 500 error when accessed

**Root Cause:** Missing `aiohttp.web` import for Response class

**Fix:** Added proper import statement and updated Response usage

**Result:** Dashboard now loads correctly at `/api/gw_smart_charging/dashboard`

**Files Changed:**
- `view.py` - Added `from aiohttp import web` and changed `self.Response` to `web.Response`

---

### 📊 Configuration Changes

#### New Configuration Options

**In UI Configuration:**
1. **Nanogreen Cheapest Sensor** (optional)
   - Entity ID of Nanogreen cheapest hours binary sensor
   - Default: empty (feature disabled)

2. **Additional Switches** (optional)
   - Comma-separated list of switch entity IDs
   - Example: `switch.heater,switch.pump`
   - Default: empty

3. **Switch Price Threshold** (optional)
   - Price threshold for additional switches in CZK/kWh
   - Default: 2.0

4. **Test Mode** (optional)
   - Enable/disable test mode
   - Default: false

**Options Flow:**
All new options are available in Options Flow (reconfiguration without reinstall)

---

### 🔄 Migration Guide

#### From v1.9.5 to v2.0.0

**No Breaking Changes** - This is a fully backward-compatible update!

1. **Update Integration**
   - Through HACS: Update to v2.0.0
   - Restart Home Assistant

2. **Optional: Configure New Features**
   - Navigate to: Settings → Devices & Services → GW Smart Charging → CONFIGURE
   - Add Nanogreen sensor (if available)
   - Add additional switches (if desired)
   - Set switch price threshold
   - Enable test mode (for testing only)

3. **Verify**
   - Check dashboard at `/api/gw_smart_charging/dashboard`
   - Verify ML is learning patterns (check logs)
   - Test additional switches (if configured)

**No data loss, no reinstallation required!**

---

### 📈 Performance Improvements

- **Faster ML Predictions** - Optimized pattern matching
- **Better Memory Management** - Separate histories prevent bloat
- **Smarter State Tracking** - Reduced unnecessary API calls

---

### 🔍 Enhanced Logging

**New Debug Information:**
- ML pattern selection (weekday/weekend/holiday)
- Nanogreen sensor state
- Additional switches state changes
- Test mode actions
- Holiday detection

**Example Logs:**
```
Using weekday patterns for ML prediction
Nanogreen sensor indicates cheapest hours - enabling charging
Turned ON switch switch.water_heater (price: 1.50 CZK/kWh, threshold: 2.00)
ML history updated: 15 weekday patterns stored
```

---

### 🎨 Dashboard Updates

**Updated Features List:**
- ✅ Advanced ML: weekday/weekend/holiday patterns
- ✅ Nanogreen cheapest hours integration
- ✅ Additional switches with price control
- ✅ Advanced testing and debugging mode
- ✅ Czech holiday detection

**Version Display:** Now shows v2.0.0

---

### 📝 Documentation

**New Documentation Files:**
- `RELEASE_NOTES_v2.0.0.md` - This file

**Updated Files:**
- `README.md` - Will be updated with v2.0 features
- `manifest.json` - Version bumped to 2.0.0

---

### 🚀 Future Enhancements (Planned for v2.1+)

Based on ROADMAP_v2.0.md:
- Weather integration for PV adjustments
- Multi-tariff support (TOU, seasonal)
- Enhanced mobile experience
- Advanced analytics dashboard
- Smart appliance coordination
- Community features

---

### 🐛 Known Issues

None reported at release time.

---

### 🙏 Acknowledgments

Thank you to all users who requested these features and provided feedback!

Special thanks to:
- Nanogreen integration users for requesting the sensor support
- Community members who suggested holiday patterns
- Beta testers who helped identify the dashboard bug

---

### 📞 Support

- **Issues:** [GitHub Issues](https://github.com/someone11221/gw_smart_energy_charging/issues)
- **Discussions:** [GitHub Discussions](https://github.com/someone11221/gw_smart_energy_charging/discussions)
- **Documentation:** [README.md](README.md)

---

### 📋 Full Changelog

**Added:**
- Nanogreen cheapest hours sensor support
- Advanced ML with weekday/weekend/holiday patterns
- Czech holiday detection
- Additional switches management
- Price-based switch control
- Test mode for debugging
- Enhanced logging for all new features
- Separate ML history tracking

**Fixed:**
- Dashboard HTTP 500 error (missing aiohttp import)

**Changed:**
- Version bumped to 2.0.0
- Dashboard features list updated
- ML prediction algorithm enhanced
- State tracking improved

**Technical:**
- Added `CONF_NANOGREEN_CHEAPEST_SENSOR` constant
- Added `CONF_ADDITIONAL_SWITCHES` constant
- Added `CONF_SWITCH_PRICE_THRESHOLD` constant
- Added `CONF_TEST_MODE` constant
- Enhanced `_execute_charging_automation()` method
- Added `_manage_additional_switches()` method
- Enhanced `_ml_predict_load_pattern()` method
- Added `_is_holiday()` method
- Enhanced `_update_ml_history()` method
- Added ML history fields: `_ml_weekday_history`, `_ml_weekend_history`, `_ml_holiday_history`

---

**Enjoy GW Smart Charging v2.0.0!** 🎉🔋⚡
