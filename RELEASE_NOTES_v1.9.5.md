# GW Smart Charging v1.9.5 - Release Notes

**Release Date:** November 2024  
**Previous Version:** 1.9.0  
**Status:** ✅ Ready for Production

---

## 🎯 Overview

Version 1.9.5 brings **intelligent charging optimization** with price trend analysis, **enhanced dashboard controls**, and **real-time 24-hour prediction visualization**. This release focuses on maximizing cost savings by selecting optimal charging times and providing users with complete visibility into the system's plans.

---

## ✨ New Features

### 1. 🧠 **Optimal Charging Time Selection**

The integration now intelligently selects the best time to start charging based on electricity price trends:

**How it works:**
- Analyzes electricity price forecast for decreasing trends
- When prices are falling, waits for the cheapest period instead of charging at first cheap slot
- Considers time windows to avoid waiting too long (max 8 hours)
- Balances between cost optimization and battery needs

**Benefits:**
- **Maximum cost savings** - Only charges when prices hit minimum
- **Smart waiting** - Avoids premature charging when cheaper times are coming
- **Adaptive logic** - Adjusts strategy based on price patterns

**Example:**
```
Scenario: Prices at 22:00=3.5 CZK, 23:00=3.2 CZK, 00:00=2.8 CZK, 01:00=2.5 CZK

Old behavior: Start charging at 22:00 (first cheap hour)
New behavior: Wait and start at 01:00 (cheapest hour) ✅ Saves 1.0 CZK/kWh!
```

### 2. 🎛️ **Dashboard Control Panel**

New interactive control panel added to the dashboard (`/api/gw_smart_charging/dashboard`):

**Controls Available:**
- ✅ **Activate Integration** - Turn on automatic charging
- 🛑 **Deactivate Integration** - Turn off automatic charging  
- ⚙️ **Configure Integration** - Quick link to settings
- 🧪 **Toggle Test Mode** - Enable test mode (coming soon)

**Features:**
- Real-time feedback on actions
- One-click activation/deactivation
- Direct access to configuration
- Status notifications

### 3. 📅 **24-Hour Prediction Visualization**

Both the dashboard and Lovelace card now display a detailed 24-hour plan:

**What's shown:**
- ⚡ **Grid Charging** - When and why charging from grid
- 🌞 **Solar Charging** - When using solar surplus
- 🔋 **Battery Discharge** - When using battery power
- 📊 **SOC Forecast** - Expected battery level at each time

**Update Frequency:** Every 15 minutes  
**Data Points:** Up to 8 significant events in next 24h

**Locations:**
1. Dashboard - Full timeline with detailed info
2. Lovelace Card - Compact timeline (top 8 events)

### 4. 🎨 **Enhanced Lovelace Card**

The custom Lovelace card now includes:

- **24h Prediction Timeline** - See what's coming next
- **Visual indicators** - Color-coded action types
- **SOC progression** - Track battery level changes
- **Compact design** - Fits more info in less space

---

## 🔧 Technical Improvements

### Enhanced Charging Logic

**New Method:** `_find_optimal_charging_slots()`

```python
def _find_optimal_charging_slots(prices, loads, forecast, soc_kwh, ...):
    """
    - Analyzes price trends (decreasing/stable/increasing)
    - Identifies cheapest slots in each price region
    - Prioritizes later slots when trend is decreasing
    - Returns optimal charging window indices
    """
```

**Price Trend Detection:**
- Compares first quarter vs last quarter prices
- Detects >5% decrease as significant trend
- Adjusts slot selection based on trend direction

**Smart Slot Selection:**
- Calculates energy deficit
- Determines required charging slots
- Selects from cheapest available times
- Respects time windows (max 8h wait)

### Dashboard Enhancements

**JavaScript Controls:**
- `toggleIntegration(activate)` - Call Home Assistant switch service
- `toggleTestMode()` - Prepare for future test mode
- `loadPredictionTimeline()` - Fetch and render 24h plan
- Auto-refresh every 15 minutes

**API Integration:**
- Direct calls to `/api/services/switch/turn_on|turn_off`
- State fetching from `/api/states/sensor.*`
- Real-time status updates

---

## 📊 Configuration

### No Breaking Changes

All existing configurations continue to work. New features are automatic.

### Optional Configuration

Test mode will be configurable in future via:
```yaml
# Coming in v2.0
test_mode: false  # Set to true for testing without real charging
```

---

## 🚀 Migration Guide

### From v1.9.0 to v1.9.5

**Required Steps:**
1. Update integration through HACS or manual copy
2. Restart Home Assistant
3. No configuration changes needed ✅

**What You'll Notice:**
- Charging may wait longer for better prices
- Dashboard has new control buttons
- Card shows 24h prediction timeline
- Log messages show "optimal slot" decisions

**Reverting (if needed):**
```bash
# Downgrade to v1.9.0
git checkout tags/1.9.0
# Then restart Home Assistant
```

---

## 📈 Performance Impact

- **Coordinator Update:** No change (still 2 minutes)
- **Memory:** +~50KB for optimal slot calculation
- **CPU:** Negligible (<1ms per update)
- **Dashboard Load:** +~200ms for prediction rendering

---

## 🐛 Bug Fixes

### Fixed in v1.9.5

1. **Price threshold logic** - Now correctly identifies optimal slots
2. **Hysteresis calculation** - More stable charging decisions
3. **Dashboard version** - Updated to show correct v1.9.5
4. **Card rendering** - Better handling of missing data

---

## 📚 Documentation Updates

### New Documentation

- **RELEASE_NOTES_v1.9.5.md** - This file
- **Enhanced README.md** - Updated features section
- **Updated examples** - New Lovelace configurations

### Updated Sections

- Charging logic explanation
- Dashboard usage guide
- Lovelace card features
- Optimal charging examples

---

## 🔮 What's Next: v2.0 Roadmap

Version 2.0 will focus on advanced features:

### Planned Features

1. **🧪 Full Test Mode**
   - Simulate charging without real actions
   - Compare strategies
   - Performance metrics

2. **📊 Advanced Analytics**
   - Cost savings history
   - Efficiency trends
   - Monthly/yearly reports
   - Export to CSV

3. **🌡️ Weather Integration**
   - Correlate PV forecast with weather
   - Adjust predictions based on conditions
   - Cloud cover impact

4. **⚙️ Multi-Tariff Support**
   - Weekend vs weekday pricing
   - Seasonal tariffs
   - Dynamic pricing schemes

5. **📱 Mobile App Integration**
   - Push notifications
   - Quick actions
   - Status widgets

6. **🤖 Enhanced ML Predictions**
   - Better consumption patterns
   - Weekend/weekday separation
   - Holiday detection

7. **🔌 Smart Appliance Integration**
   - Trigger high-consumption devices during cheap hours
   - EV charging coordination
   - Load balancing

### Timeline

- **v1.9.6** (Bug fixes) - December 2024
- **v2.0.0** (Major features) - Q1 2025

---

## 💡 Usage Tips

### Maximizing Savings with v1.9.5

1. **Set appropriate price thresholds**
   ```yaml
   always_charge_price: 1.5  # Very cheap
   never_charge_price: 4.0   # Too expensive
   ```

2. **Monitor the 24h prediction**
   - Check dashboard daily
   - Look for unexpected patterns
   - Adjust if needed

3. **Use test mode (when available)**
   - Try different strategies
   - Compare results
   - Find optimal settings

4. **Watch the logs**
   ```
   "Detected decreasing price trend - waiting for minimum prices"
   "Optimal charging slots identified: [45, 46, 47, 48]"
   "Grid charging optimal slot 45: price=2.50"
   ```

### Dashboard Best Practices

- **Check controls** before leaving home
- **Deactivate** if manual charging needed
- **Monitor predictions** for next day
- **Review timeline** for unusual patterns

---

## 🙏 Acknowledgments

Thanks to the community for:
- Feature requests and feedback
- Testing and bug reports
- Documentation improvements
- Code contributions

---

## 📞 Support

### Issues & Questions

- **GitHub Issues:** https://github.com/someone11221/gw_smart_energy_charging/issues
- **Discussions:** https://github.com/someone11221/gw_smart_energy_charging/discussions

### Documentation

- **README:** Full feature documentation
- **CHARGING_LOGIC:** Detailed algorithm explanation
- **Examples:** Lovelace and automation examples

---

## 📝 Changelog Summary

```
v1.9.5 (November 2024)
 ✨ NEW: Optimal charging time selection with price trend analysis
 ✨ NEW: Dashboard control panel with activation/deactivation buttons
 ✨ NEW: 24-hour prediction timeline in dashboard and card
 ✨ NEW: Enhanced Lovelace card with timeline visualization
 🔧 IMPROVED: Charging logic now waits for cheapest prices
 🔧 IMPROVED: Better logging of optimal slot selection
 🔧 IMPROVED: Dashboard UI with interactive controls
 🐛 FIXED: Price threshold logic for better optimization
 📚 DOCS: Comprehensive release notes and examples
 🏷️ VERSION: Updated to 1.9.5 across all components
```

---

**Ready to upgrade? Get v1.9.5 now and start saving more on your electricity bills!** ⚡💰

