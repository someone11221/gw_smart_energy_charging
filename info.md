# GW Smart Charging

**Optimize your GoodWe battery charging with smart scheduling based on solar forecasts and electricity prices.**

## What It Does

GW Smart Charging automatically manages your GoodWe inverter's battery charging to minimize electricity costs while maximizing the use of solar energy.

### Key Features

- **Smart Optimization**: Calculates optimal 24-hour charging schedule based on:
  - Solar PV forecast for the next day
  - Hourly electricity prices
  - Current battery state of charge
  - Battery capacity and charging efficiency

- **Automatic Control**: Manages GoodWe grid charging switch automatically to:
  - Charge from grid during cheapest hours when needed
  - Prioritize solar charging when PV production is available
  - Maintain minimum battery reserve levels

- **Easy Configuration**: UI-based setup through Home Assistant's integration interface - no YAML editing required

- **Manual Services**: Two service calls for manual control:
  - `gw_smart_charging.optimize_now` - Recalculate schedule on demand
  - `gw_smart_charging.apply_schedule_now` - Apply current hour's schedule immediately

## Installation via HACS

1. Add this repository as a custom repository in HACS:
   - HACS → Integrations → ⋮ (menu) → Custom repositories
   - Repository: `https://github.com/someone11221/gw_smart_energy_charging`
   - Category: Integration

2. Install "GW Smart Charging" from HACS

3. Restart Home Assistant

4. Add the integration:
   - Settings → Devices & Services → Add Integration
   - Search for "GW Smart Charging"

## Requirements

- GoodWe inverter with Home Assistant integration
- Solar forecast sensor (e.g., ha-open-meteo-solar-forecast)
- Electricity price sensor (e.g., nanogreencz integration)
- Battery state of charge sensor

## Configuration

During setup, you'll configure:

- **Sensors**: Forecast, price, PV power, and battery SOC sensors
- **GoodWe Switch**: Entity for controlling grid charging
- **Battery Parameters**: Capacity, max charge power, efficiency
- **Preferences**: Minimum reserve percentage, automation enable/disable

## How the Schedule Works

The integration creates a sensor `sensor.forecast_next_day` with a schedule attribute containing 24 hourly entries. Each entry shows the planned charging mode:

- **pv**: Charge from solar only
- **grid**: Charge from grid (during cheap hours)
- **idle**: No charging needed

The schedule is recalculated automatically and can be reviewed in the sensor attributes. Historical schedules are stored by Home Assistant's recorder.

## Debug Logging

To enable debug logging, add to your `configuration.yaml`:

```yaml
logger:
  default: warning
  logs:
    custom_components.gw_smart_charging: debug
```

## Support & Issues

Found a bug or have a feature request? Please open an issue on [GitHub](https://github.com/someone11221/gw_smart_energy_charging/issues).

---

*For detailed documentation, see the [GitHub repository](https://github.com/someone11221/gw_smart_energy_charging).*
