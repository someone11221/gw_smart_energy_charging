# GW Smart Charging v2.1.0 Release Notes

**Release Date:** November 2024  
**Major Update - Enhanced Dashboard, Charging Strategies & Improved Logic**

---

## 🎉 What's New in v2.1.0

Version 2.1.0 brings significant improvements to the dashboard, introduces multiple charging strategies, and enhances the battery charging logic with smarter price optimization.

---

## 🔧 Fixed Issues

### Dashboard 24-Hour Prediction Plan Fixed
**FIXED:** Dashboard JSON parsing error that prevented 24-hour prediction timeline from loading

**What was the problem:**
- Dashboard tried to fetch schedule data via unauthenticated API call
- Browser received HTML login page instead of JSON
- Error: "Unexpected non-whitespace character after JSON at position 3"

**How it's fixed:**
- Schedule data now embedded directly in HTML from backend
- No more client-side API calls requiring authentication
- Proper fallback messages when data is not yet available
- More reliable and faster loading

### Activate/Deactivate Buttons Fixed
**FIXED:** Integration control buttons not working properly

**What was the problem:**
- Buttons didn't include authentication headers
- API calls were rejected by Home Assistant
- No visual feedback on button state

**How it's fixed:**
- Added automatic authentication token retrieval
- Proper Authorization headers on all API calls
- Visual feedback showing enabled/disabled button states
- Automatic page reload after successful toggle
- Better error messages for debugging

---

## ⚡ Enhanced Charging Logic

### Improved 12-Hour Price Lookahead
**ENHANCED:** Smarter battery charging with better price trend detection

**What's improved:**
- Changed from 24-hour to **12-hour lookahead window** for more focused optimization
- **10% price decrease threshold** - only waits if prices will drop by at least 10%
- **Smart waiting logic** - only delays charging if cheapest prices are at least 1 hour away
- Better comparison of current price vs future price averages
- More accurate trend detection prevents unnecessary waiting

**Example scenario:**
```
Current time: 22:00, SOC: 45%, Target: 90%
Prices: 22:00=3.5 CZK, 23:00=3.2 CZK, 00:00=2.8 CZK, 01:00=2.5 CZK

Old behavior (v2.0): Might start charging at 22:00
New behavior (v2.1): Detects 10%+ drop, waits until 01:00
Result: Save 1.0 CZK/kWh! 💰
```

---

## 🎯 Charging Strategy Selector

**NEW:** Choose from 5 different charging strategies to match your needs!

### Available Strategies

#### 1. **Dynamic Optimization** (Default) ⚡
- Smart optimization based on prices, forecasts, and consumption patterns
- Uses ML predictions and trend analysis
- Waits for best prices when trend is decreasing
- Best for: Most users wanting maximum savings

#### 2. **4 Lowest Hours** 📊
- Always charge during the 4 cheapest hours in next 24h
- Simple and predictable
- Best for: Users who want consistent charging times

#### 3. **6 Lowest Hours** 📊
- Always charge during the 6 cheapest hours in next 24h
- More charging opportunities
- Best for: Larger batteries or higher consumption

#### 4. **Nanogreen Only** 🎛️
- Use only Nanogreen sensor for charging decisions
- Charge when `sensor.is_currently_in_five_cheapest_hours` is ON
- Best for: Users who trust Nanogreen integration exclusively

#### 5. **Price Threshold** 💰
- Charge whenever price drops below "Always Charge Price"
- Most aggressive charging
- Best for: Users with very cheap night tariffs

### How to Configure

**Via UI:**
1. Go to Settings → Devices & Services
2. Find "GW Smart Charging"
3. Click CONFIGURE
4. Select "Charging Strategy" from dropdown
5. Save

**Strategies are available in:**
- Initial setup flow
- Options flow (reconfiguration)
- Clearly labeled in UI

---

## 📦 Version Updates

### Consistent Versioning Across All Components
**UPDATED:** All integration components now show version 2.1.0

- ✅ manifest.json → 2.1.0
- ✅ Dashboard → 2.1.0
- ✅ Lovelace Card → 2.1.0
- ✅ All documentation → 2.1.0

**Why this matters:**
- Easy to verify which version you're running
- Consistent version reporting in logs
- Better troubleshooting and support

---

## 🛠️ Technical Improvements

### Enhanced Configuration Flow
- Added charging strategy selector to setup wizard
- Added to options flow for easy reconfiguration
- New configuration fields in strings.json
- Proper validation and defaults

### Improved Logging
- Strategy selection logged at INFO level
- Better debugging for price trend detection
- Clear messages about why charging is delayed or activated

### Code Quality
- New strategy abstraction layer in coordinator
- Cleaner separation of concerns
- Each strategy in its own function
- Better maintainability and testability

---

## 📝 Configuration Changes

### New Configuration Options

**Charging Strategy** (`charging_strategy`)
- Type: Selection
- Options: `dynamic`, `4_lowest_hours`, `6_lowest_hours`, `nanogreen_only`, `price_threshold`
- Default: `dynamic`
- Available in: Setup flow, Options flow

### Backward Compatibility

**✅ Fully backward compatible with v2.0.0**
- All existing configurations continue to work
- Default strategy is dynamic (same as v2.0 behavior)
- No breaking changes
- No data loss on upgrade

---

## 🚀 Upgrade Guide

### From v2.0.0 to v2.1.0

**Recommended upgrade steps:**

1. **Backup your configuration** (optional but recommended)
   - Settings → Devices & Services → GW Smart Charging
   - Note your current settings

2. **Update via HACS**
   - HACS → Integrations
   - Find "GW Smart Charging"
   - Click UPDATE

3. **Restart Home Assistant**
   - Settings → System → Restart

4. **Verify the upgrade**
   - Check dashboard shows v2.1.0
   - Test activate/deactivate buttons
   - Check 24h prediction plan loads correctly

5. **Optional: Configure charging strategy**
   - Settings → Devices & Services → GW Smart Charging → CONFIGURE
   - Select your preferred strategy
   - Save

**That's it!** The integration will continue working with smart defaults.

---

## 🐛 Bug Fixes Summary

| Issue | Status | Solution |
|-------|--------|----------|
| Dashboard JSON parsing error | ✅ Fixed | Data embedded in HTML |
| Activate/Deactivate buttons not working | ✅ Fixed | Added auth headers |
| Price trend detection too conservative | ✅ Improved | 12h window + 10% threshold |
| Version inconsistency | ✅ Fixed | All components show 2.1.0 |

---

## 🔮 What's Next?

### Planned for v2.2.0+
- 🇨🇿 Czech language support
- 🌍 Language toggle (CZ/EN)
- 📊 Interactive graphs in dashboard
- 📝 Enhanced activity logging
- 🎨 Improved dashboard UI/UX
- 🔌 UI for negative price switch configuration

---

## 📚 Documentation Updates

### Updated Files
- ✅ README.md - Added v2.1.0 features
- ✅ RELEASE_NOTES_v2.1.0.md - This file
- ✅ All version references updated

### Need Help?

**Documentation:**
- GitHub: https://github.com/someone11221/gw_smart_energy_charging
- README: Comprehensive setup and features guide

**Support:**
- GitHub Issues: Report bugs or request features
- Community: Share experiences and configurations

---

## 💡 Tips for v2.1.0

### Getting the Best Results

**For Maximum Savings:**
- Use "Dynamic Optimization" strategy (default)
- Set appropriate price thresholds (Always Charge / Never Charge)
- Enable ML prediction for better consumption forecasts

**For Predictable Behavior:**
- Use "4 Lowest Hours" or "6 Lowest Hours" strategy
- Check schedule in dashboard before peak hours
- Monitor daily statistics sensor

**For Nanogreen Users:**
- Use "Nanogreen Only" strategy if you trust it fully
- Or keep "Dynamic" for best of both worlds
- Monitor when both systems agree for highest confidence

### Troubleshooting

**Dashboard not loading?**
- Clear browser cache
- Hard refresh (Ctrl+F5 or Cmd+Shift+R)
- Check Home Assistant logs for errors

**Buttons not working?**
- Make sure you're logged into Home Assistant
- Check browser console for auth errors
- Verify integration switch entity exists

**Strategy not applying?**
- Check configuration saved properly
- Restart integration after changes
- Monitor logs for strategy selection messages

---

## 🙏 Credits

**Contributors:**
- @someone11221 - Core development and integration architecture
- Community feedback and testing

**Special Thanks:**
- Home Assistant community
- All beta testers and early adopters

---

## 📄 License

This integration is released under the same license as the main repository.

---

**Enjoy GW Smart Charging v2.1.0! ⚡🔋💚**

For questions, issues, or feature requests, please visit our GitHub repository.
