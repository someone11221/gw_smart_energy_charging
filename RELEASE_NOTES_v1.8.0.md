# Release Notes v1.8.0

## GW Smart Charging v1.8.0 - Entity Consolidation & Device Integration

**Release Date:** November 2024

### 🎯 Major Improvements

#### Device Integration
- **✨ Device Panel Support** - Integration now appears in Home Assistant's Devices & Services panel
  - Shows all sensors and controls in one organized place
  - Easy access to all entities from device page
  - Activity, configuration, and diagnostics in one view

#### Entity Consolidation
- **📊 Reduced Entity Count** - Simplified from 21 to 9 core entities
  - Removed 6 redundant series sensors (data moved to attributes)
  - Merged today's charge/discharge into battery power sensor
  - Consolidated next charge and discharge into single sensor
  - Removed separate status and price sensors (merged into forecast)
  
#### Enhanced Sensors

**`sensor.gw_smart_charging_forecast`**
- Now includes price information in attributes
- Shows current price alongside forecast
- Displays total forecast and peak values
- Single source for forecast and pricing data

**`sensor.gw_smart_charging_soc_forecast`**
- Now includes all series data for charting
- Attributes: `pv_series_kw`, `load_series_kw`, `battery_charge_series_kw`, `battery_discharge_series_kw`, `grid_import_series_kw`
- Replaces 6 separate series sensors
- More organized data structure

**`sensor.gw_smart_charging_battery_power`**
- Enhanced with SOC information
- Includes today's charge and discharge totals
- Shows net daily energy (charge - discharge)
- Consolidated battery metrics in one place

**`sensor.gw_smart_charging_schedule`**
- Now includes next charge and discharge times
- Simplified schedule viewing
- Consolidated scheduling information

**`sensor.gw_smart_charging_next_charge`**
- Combined next grid charge and battery discharge
- Single sensor for all upcoming periods
- Separate attributes for charge and discharge schedules
- Cleaner automation integration

**`sensor.gw_smart_charging_diagnostics`**
- **🔧 Fixed:** Now shows correct current SOC in state
- Displays: `status - mode (SoC: XX.X%)`
- Accurate SOC from `sensor.battery_state_of_charge`
- Comprehensive diagnostic information

### 📚 Documentation

#### New: CHARGING_LOGIC.md
- **Complete charging logic documentation**
- Detailed sensor descriptions and usage
- Step-by-step decision making process
- Example scenarios for different times of day
- Configuration parameter explanations
- Benefits and optimization strategies

### 🔧 Technical Changes

#### Device Info
- All entities now have `device_info` property
- Grouped under single device in Home Assistant
- Manufacturer: "GW Energy Solutions"
- Model: "Smart Battery Charging Controller"
- Software version tracking

#### Code Quality
- Improved code organization
- Better attribute grouping
- Reduced code duplication
- More maintainable structure

### 📋 Migration Guide

If upgrading from v1.7.0:

#### Removed Entities (Data Available in Other Sensors)
- `sensor.gw_smart_charging_forecast_status` → See `sensor.gw_smart_charging_diagnostics`
- `sensor.gw_smart_charging_price` → See `sensor.gw_smart_charging_forecast` attributes
- `sensor.gw_smart_charging_today_battery_charge` → See `sensor.gw_smart_charging_battery_power` attributes
- `sensor.gw_smart_charging_today_battery_discharge` → See `sensor.gw_smart_charging_battery_power` attributes
- `sensor.gw_smart_charging_next_battery_discharge` → See `sensor.gw_smart_charging_next_charge` attributes
- `sensor.gw_smart_charging_series_pv` → See `sensor.gw_smart_charging_soc_forecast` attributes
- `sensor.gw_smart_charging_series_load` → See `sensor.gw_smart_charging_soc_forecast` attributes
- `sensor.gw_smart_charging_series_battery_charge` → See `sensor.gw_smart_charging_soc_forecast` attributes
- `sensor.gw_smart_charging_series_battery_discharge` → See `sensor.gw_smart_charging_soc_forecast` attributes
- `sensor.gw_smart_charging_series_grid_import` → See `sensor.gw_smart_charging_soc_forecast` attributes
- `sensor.gw_smart_charging_series_soc_forecast` → See `sensor.gw_smart_charging_soc_forecast` attributes

#### Updated Automations/Dashboards
If you used removed sensors:

**For chart data:**
```yaml
# Old way (v1.7.0)
- entity: sensor.gw_smart_charging_series_pv
  attribute: data_15min
  
# New way (v1.8.0)
- entity: sensor.gw_smart_charging_soc_forecast
  attribute: pv_series_kw
```

**For today's totals:**
```yaml
# Old way (v1.7.0)
- entity: sensor.gw_smart_charging_today_battery_charge

# New way (v1.8.0)
- entity: sensor.gw_smart_charging_battery_power
  attribute: today_charge_kwh
```

**For current price:**
```yaml
# Old way (v1.7.0)
- entity: sensor.gw_smart_charging_price

# New way (v1.8.0)
- entity: sensor.gw_smart_charging_forecast
  attribute: current_price_czk_kwh
```

### 🎨 Current Entity List (v1.8.0)

#### Sensors (9)
1. `sensor.gw_smart_charging_forecast` - Solar forecast with pricing
2. `sensor.gw_smart_charging_schedule` - Current schedule and mode
3. `sensor.gw_smart_charging_soc_forecast` - SOC forecast with series data
4. `sensor.gw_smart_charging_battery_power` - Battery metrics and totals
5. `sensor.gw_smart_charging_diagnostics` - System status and diagnostics
6. `sensor.gw_smart_charging_daily_statistics` - Daily stats and savings
7. `sensor.gw_smart_charging_prediction` - ML prediction quality
8. `sensor.gw_smart_charging_next_charge` - Upcoming charge/discharge periods
9. `sensor.gw_smart_charging_activity_log` - Activity history

#### Switch (1)
10. `switch.gw_smart_charging_auto_charging` - Automatic control

### 💡 Benefits of v1.8.0

- **Cleaner UI**: Fewer entities, better organized
- **Device Integration**: All controls in one device panel
- **Easier Navigation**: Find everything in device page
- **Better Understanding**: Clear sensor names and purposes
- **Comprehensive Docs**: Full charging logic explained
- **Fixed Diagnostics**: Accurate SOC display
- **Simplified Automation**: Consolidated attributes

### 🔜 Future Enhancements Suggested

1. **Energy Dashboard Integration**
   - Native integration with HA Energy dashboard
   - Track charging costs and savings
   
2. **Advanced Notifications**
   - Alert when battery SOC is critical
   - Notify about unusual consumption patterns
   
3. **Tariff Support**
   - Multi-tariff pricing support
   - Time-of-use rate optimization
   
4. **Weather Integration**
   - Combine weather forecast with solar prediction
   - Adjust for cloudy days
   
5. **Historical Analytics**
   - Long-term efficiency tracking
   - Charging pattern analysis
   - Cost savings reports

### 📞 Support

For issues or questions:
- GitHub Issues: https://github.com/someone11221/gw_smart_energy_charging/issues
- Documentation: See CHARGING_LOGIC.md for detailed explanations
- Community Forum: Home Assistant Community

---

**Upgrade Note**: This release includes breaking changes in entity names. Please update your dashboards and automations accordingly. All data is still available, just in consolidated form.
