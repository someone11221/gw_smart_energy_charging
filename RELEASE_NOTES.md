# Release Notes

## v1.0.0 - Initial HACS-Compatible Release

### Overview
This is the first official release of GW Smart Charging, now fully compatible with HACS (Home Assistant Community Store) and ready for easy installation.

### Features
- **Smart Battery Charging Optimization**: Automatically optimizes GoodWe battery charging based on solar forecast and electricity prices
- **24-Hour Planning**: Creates intelligent charging schedules for the next 24 hours
- **Config Flow Support**: Easy setup through Home Assistant UI (Settings → Devices & Services → Add Integration)
- **Automation Services**: 
  - `gw_smart_charging.optimize_now` - Force schedule recalculation
  - `gw_smart_charging.apply_schedule_now` - Immediately apply current hour's schedule
- **Flexible Configuration**: Supports various sensors for forecast, prices, PV power, SOC, and GoodWe switch control

### Installation

#### Via HACS (Recommended)
1. Open HACS in Home Assistant
2. Go to Integrations
3. Click the three dots in the top right corner
4. Select "Custom repositories"
5. Add repository URL: `https://github.com/someone11221/gw_smart_energy_charging`
6. Select category: Integration
7. Click "Download" on GW Smart Charging
8. Restart Home Assistant
9. Add the integration: Settings → Devices & Services → Add Integration → "GW Smart Charging"

#### Manual Installation
1. Copy the `custom_components/gw_smart_charging` folder to your Home Assistant `config/custom_components/` directory
2. Restart Home Assistant
3. Add the integration through the UI

### Configuration
The integration uses UI-based configuration with the following options:
- **forecast_sensor**: 24-hour solar PV forecast sensor
- **price_sensor**: 24-hour electricity price sensor
- **pv_power_sensor**: (Optional) Current PV power sensor
- **goodwe_switch**: GoodWe switch entity for grid charging control
- **soc_sensor**: Battery state of charge sensor
- **battery_capacity_kwh**: Battery capacity in kWh (default: 17)
- **max_charge_power_kw**: Maximum charging power in kW (default: 3.7)
- **charge_efficiency**: Charging efficiency (default: 0.95)
- **min_reserve_pct**: Minimum battery reserve percentage (default: 10%)
- **enable_automation**: Enable automatic switch control (default: true)
- **switch_on_means_charge**: Whether switch ON means charging from grid (default: true)

### How It Works
1. Reads solar forecast and electricity prices for the next 24 hours
2. Calculates required battery charge to reach 100% (respecting minimum reserve)
3. Prioritizes solar PV utilization during production hours
4. Schedules grid charging during cheapest hours for remaining energy needs
5. Exposes sensor with charging schedule in attributes
6. Optionally controls GoodWe switch automatically based on schedule

### Requirements
- Home Assistant 2025.1.0 or later
- GoodWe integration installed and configured
- Solar forecast sensor (e.g., ha-open-meteo-solar-forecast)
- Electricity price sensor (e.g., nanogreencz integration)

### Compatibility
- Home Assistant: 2025.1.0+
- HACS: Compatible
- Quality Scale: Platinum

### Known Issues
None at this time.

### Upgrade Instructions
This is the first release. For users who manually installed development versions:
1. Uninstall any previous manual installations
2. Remove old folders from `config/custom_components/`
3. Restart Home Assistant
4. Install via HACS as described above
5. Reconfigure the integration through the UI

### Support
- Issues: https://github.com/someone11221/gw_smart_energy_charging/issues
- Documentation: https://github.com/someone11221/gw_smart_energy_charging

### Contributors
- @someone11221

### License
See LICENSE file for details.
