# GW Smart Charging

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)

GW Smart Charging is a Home Assistant custom integration that connects GoodWe inverters with solar forecasts and electricity prices to optimize battery charging and minimize costs.

## Features

- 24-hour charging schedule optimization based on PV forecast and electricity prices
- Automatic battery charging management via GoodWe switch control
- UI-based configuration flow (no YAML required)
- Support for custom solar forecast and price sensors
- Services for manual optimization and schedule application
- Integration with Home Assistant's recorder for historical data

## Installation via HACS

1. Open HACS in your Home Assistant instance
2. Go to "Integrations" section
3. Click the three dots in the top right corner and select "Custom repositories"
4. Add repository URL: `https://github.com/someone11221/gw_smart_energy_charging`
5. Select category: "Integration"
6. Click "Add"
7. Find "GW Smart Charging" in the integrations list and click "Download"
8. Restart Home Assistant
9. Go to Settings → Devices & Services → Add Integration
10. Search for "GW Smart Charging" and follow the configuration steps

## Configuration

The integration uses a UI-based config flow. You'll need to provide:

- **forecast_sensor**: 24-hour PV forecast sensor (e.g., from ha-open-meteo-solar-forecast)
- **price_sensor**: 24-hour electricity price sensor (e.g., from nanogreencz integration)
- **pv_power_sensor**: (optional) Current PV power output sensor
- **soc_sensor**: Battery state of charge sensor (default: sensor.battery_state_of_charge)
- **goodwe_switch**: GoodWe switch entity for grid charging control (default: switch.nabijeni_ze_site)
- **battery_capacity_kwh**: Battery capacity in kWh (default: 17)
- **max_charge_power_kw**: Maximum charging power in kW
- **charge_efficiency**: Charging efficiency (default: 0.95)
- **min_reserve_pct**: Minimum battery reserve percentage (default: 10%)
- **enable_automation**: Enable automatic switch control (default: true)

## Services

- `gw_smart_charging.optimize_now` - Force immediate optimization calculation
- `gw_smart_charging.apply_schedule_now` - Apply current hour's schedule immediately

## How It Works

1. The integration fetches the 24-hour PV forecast and electricity prices
2. Calculates optimal charging schedule to reach 100% SOC while minimizing costs
3. Prioritizes using PV power when available
4. Charges from grid during cheapest hours when needed
5. Exposes a sensor with the schedule as an attribute
6. Automatically controls the GoodWe switch based on the schedule (if automation enabled)

## Support

- [Issue Tracker](https://github.com/someone11221/gw_smart_energy_charging/issues)
- [Documentation](https://github.com/someone11221/gw_smart_energy_charging)

## License

See LICENSE file for details.
