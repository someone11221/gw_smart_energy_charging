# GW Smart Charging v2.2.0 Release Notes

**Release Date:** November 2024  
**Major Update - Enhanced Charging Strategies, Multi-Language Support & Interactive Dashboard**

---

## 🎉 What's New in v2.2.0

Version 2.2.0 represents a significant evolution of GW Smart Charging with **4 new charging strategies**, **Czech/English language support**, and a **completely redesigned interactive dashboard** with real-time graphs powered by Chart.js.

---

## 🆕 New Features

### 1. Multi-Language Support (Czech/English)
**NEW:** Complete bilingual interface support

**Features:**
- **Language Toggle** - Switch between Czech (Čeština) and English
- **Dashboard Translation** - All UI elements translated
- **Chart Labels** - Charts display in selected language
- **Configuration UI** - Setup wizard supports both languages
- **Automatic Detection** - Remembers language preference per installation

**How to Use:**
1. Navigate to Settings → Devices & Services → GW Smart Charging
2. Click **CONFIGURE**
3. Select your preferred language: "cs" (Czech) or "en" (English)
4. Dashboard and all interfaces will update automatically

---

### 2. Four New Charging Strategies
**NEW:** Total of 9 charging strategies to choose from!

#### Strategy 6: Adaptive Smart 🧠
- **Purpose:** Learns from past consumption patterns
- **How it works:** Uses ML predictions combined with price optimization
- **Best for:** Users with consistent daily routines
- **Key feature:** Prioritizes charging before predicted high consumption periods

#### Strategy 7: Solar Priority ☀️
- **Purpose:** Maximize solar self-consumption
- **How it works:** Charges mainly when solar forecast is high
- **Best for:** Maximizing use of own solar production
- **Key feature:** Avoids grid charging unless absolutely necessary

#### Strategy 8: Peak Shaving 📊
- **Purpose:** Avoid grid during peak hours
- **How it works:** Ensures battery charged before peak consumption hours
- **Best for:** Reducing demand charges and peak hour costs
- **Key feature:** Prioritizes cheapest off-peak hours for charging

#### Strategy 9: Time-of-Use Optimized ⚡
- **Purpose:** Optimized for TOU tariffs
- **How it works:** Identifies price tiers and charges only in lowest tier
- **Best for:** Users with TOU electricity tariffs
- **Key feature:** Automatically detects and avoids high-price periods

**All strategies available in:**
- Initial setup wizard
- Configuration options (Settings → Configure Integration)

---

### 3. Full-Hour Charging Cycles
**NEW:** Charging now operates in full 1-hour blocks

**What changed:**
- **Before v2.2.0:** Could charge in individual 15-minute slots
- **Now v2.2.0:** Charges in complete 1-hour blocks (4 consecutive 15-min slots)
- **Benefit:** More stable charging cycles, better for battery health
- **Configuration:** `full_hour_charging` option (enabled by default)

**How it works:**
```
Example: Strategy selects 4 cheapest hours
Old behavior: Could select slots at 10:15, 14:00, 18:30, 22:45
New behavior: Selects hours 22:00-23:00, 23:00-00:00, 01:00-02:00, 02:00-03:00
```

**Key advantages:**
- ✅ Consistent hourly charging patterns
- ✅ Reduced switching between charge/discharge
- ✅ Better battery cycle management
- ✅ Still uses 15-min granularity for price analysis

---

### 4. Interactive Dashboard with Charts
**NEW:** Completely redesigned dashboard with real-time graphs

**Three Dynamic Charts:**

#### Chart 1: Price & Charging Schedule 📈
- **Shows:** Electricity prices over 24 hours
- **Overlay:** Green markers show planned charging periods
- **Updates:** Every 15 minutes
- **Interactive:** Hover to see exact values
- **Use:** Visualize when system will charge vs prices

#### Chart 2: SOC Forecast 🔋
- **Shows:** Predicted battery state of charge over 24h
- **Range:** 0-100%
- **Updates:** Based on current schedule
- **Use:** See how battery level will change throughout day

#### Chart 3: Solar Production 🌞
- **Shows:** Expected solar energy production
- **Type:** Bar chart showing hourly production
- **Units:** kWh per 15-minute interval
- **Use:** Plan charging around solar availability

**Chart Features:**
- Responsive design (works on mobile & desktop)
- Zoom and pan capabilities
- Downloadable chart images
- Auto-refresh with data updates
- Language-aware labels

---

## ⚡ Enhanced Existing Features

### Improved Price Optimization
All strategies now use enhanced price sorting:
- **24-hour price ranking** - Finds absolute lowest prices
- **Full-hour averaging** - Compares average price across 4 slots
- **Trend detection** - Identifies price decrease patterns
- **Smart waiting** - Delays charging if prices will drop further

### Better Strategy Selection
Each strategy now includes:
- **Clear description** - Explains when to use it
- **Visual indicators** - Icons show strategy type
- **Performance hints** - Suggests best use cases
- **Easy switching** - Change via Options Flow without reinstall

---

## 🔧 Technical Improvements

### Code Enhancements
- **New translations.py module** - Centralized translation management
- **Optimized coordinator** - Better performance with new strategies
- **Enhanced config_flow** - Improved UI for strategy selection
- **Chart.js integration** - Professional-grade charting library

### Configuration Options
New options in setup wizard:
- `language` - Select Czech or English (default: Czech)
- `full_hour_charging` - Enable full-hour charging cycles (default: True)
- `charging_strategy` - Now includes 9 strategies (default: Dynamic)

---

## 📊 Comparison of All 9 Strategies

| Strategy | Complexity | Best For | Grid Usage | Solar Focus |
|----------|-----------|----------|------------|-------------|
| 1. Dynamic Optimization | High | Maximum savings | Smart | Medium |
| 2. 4 Lowest Hours | Low | Predictability | Moderate | Low |
| 3. 6 Lowest Hours | Low | Larger batteries | Higher | Low |
| 4. Nanogreen Only | Low | Nanogreen users | Smart | Low |
| 5. Price Threshold | Medium | Cheap tariffs | Aggressive | Low |
| 6. Adaptive Smart | High | Routine users | Smart | Medium |
| 7. Solar Priority | Medium | Solar maximization | Minimal | **High** |
| 8. Peak Shaving | Medium | Peak avoidance | Off-peak | Low |
| 9. TOU Optimized | Medium | TOU tariffs | Low-tier only | Low |

---

## 🎯 Migration from v2.1.0

**Good News: Fully backward compatible!**

### No Action Required
- All existing configurations work without changes
- Default strategy remains "Dynamic Optimization"
- No data loss or reconfiguration needed
- Automatic version upgrade

### Optional Enhancements
After upgrading, you can optionally:

1. **Select Language:**
   - Go to Settings → Configure Integration
   - Choose Czech or English

2. **Try New Strategies:**
   - Access via Options Flow
   - Test different strategies
   - Find best fit for your usage

3. **View New Dashboard:**
   - Navigate to `/api/gw_smart_charging/dashboard`
   - Explore interactive charts
   - Monitor real-time charging decisions

---

## 🐛 Bug Fixes

### Chart Loading
- Fixed potential null data handling in charts
- Added fallback messages when data not available
- Improved error handling for missing sensors

### Language Display
- Ensured consistent language across all UI elements
- Fixed translation key resolution
- Added missing Czech translations

---

## 📝 Configuration Examples

### Example 1: Solar-Focused Setup
```yaml
language: en
charging_strategy: solar_priority
full_hour_charging: true
target_soc_pct: 90
always_charge_price: 1.5
```

### Example 2: Cost-Optimized Setup
```yaml
language: cs
charging_strategy: tou_optimized
full_hour_charging: true
target_soc_pct: 85
always_charge_price: 2.0
```

### Example 3: Peak-Shaving Setup
```yaml
language: en
charging_strategy: peak_shaving
full_hour_charging: true
critical_hours_start: 17
critical_hours_end: 21
target_soc_pct: 90
```

---

## 🔮 Looking Ahead

Features planned for v2.3.0:
- Export/import configuration
- Custom strategy builder
- Battery health monitoring
- Cost savings calculator
- Weather integration
- Advanced forecasting

---

## 📚 Documentation

### Updated Documentation
- README.md - Updated with v2.2.0 features
- IMPLEMENTATION_v2.2.0.md - Technical implementation details
- examples/ - New configuration examples

### API Changes
No breaking changes to existing APIs.

New coordinator methods:
- `_strategy_adaptive_smart()`
- `_strategy_solar_priority()`
- `_strategy_peak_shaving()`
- `_strategy_tou_optimized()`
- `_find_n_cheapest_hours()`

---

## 🙏 Acknowledgments

Thanks to all users who requested these features:
- Multi-language support
- More charging strategies
- Enhanced dashboard visualization
- Full-hour charging cycles

---

## 📦 Installation

### HACS Installation
1. Ensure HACS is installed
2. Add custom repository: `https://github.com/someone11221/gw_smart_energy_charging`
3. Install "GW Smart Charging"
4. Restart Home Assistant
5. Add integration via Settings → Devices & Services

### Manual Installation
1. Download latest release
2. Copy `custom_components/gw_smart_charging` to your config directory
3. Restart Home Assistant
4. Add integration

---

## 🆘 Support

For issues, questions, or feature requests:
- **GitHub Issues:** https://github.com/someone11221/gw_smart_energy_charging/issues
- **Documentation:** See README.md and implementation notes
- **Community:** Share your setup and strategies!

---

**Enjoy GW Smart Charging v2.2.0! 🎉🔋⚡**
