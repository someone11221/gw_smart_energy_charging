# Release Notes

## Version 1.0.0 - Initial HACS Release

This is the first official HACS-compatible release of GW Smart Charging.

### Features

- **Smart Battery Optimization**: 24-hour charging schedule based on solar forecast and electricity prices
- **UI Configuration Flow**: Easy setup through Home Assistant's integration interface
- **Automatic Control**: Optional automatic control of GoodWe grid charging switch
- **Manual Services**: 
  - `gw_smart_charging.optimize_now` - Force schedule recalculation
  - `gw_smart_charging.apply_schedule_now` - Apply current schedule immediately
- **Sensor Integration**: Exposes schedule data through Home Assistant sensors with recorder support

### Configuration Options

- Solar forecast sensor integration
- Electricity price sensor integration
- Optional PV power monitoring
- Battery capacity and efficiency settings
- Minimum reserve percentage configuration
- Customizable GoodWe switch entity

### Requirements

- Home Assistant 2025.1.0 or later
- GoodWe integration installed and configured
- Solar forecast sensor (e.g., ha-open-meteo-solar-forecast)
- Electricity price sensor (e.g., nanogreencz)

### Installation

Install via HACS:
1. Add custom repository: `https://github.com/someone11221/gw_smart_energy_charging`
2. Install "GW Smart Charging" integration
3. Restart Home Assistant
4. Configure via Settings → Devices & Services → Add Integration

### Known Limitations

- Requires manual configuration of sensor entities
- Optimization runs on a fixed schedule (can be triggered manually)
- Supports GoodWe inverters only

### Support

For issues, feature requests, or questions, please visit:
https://github.com/someone11221/gw_smart_energy_charging/issues