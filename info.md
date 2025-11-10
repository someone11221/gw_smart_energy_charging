# GW Smart Charging v1.4.0

GW Smart Charging automatizuje nabíjení baterie GoodWe podle 15minutových cen a solárního forecastu s aktivním řízením každé 2 minuty.

## Co dělá
- **Automatické volání skriptů** - Každé 2 minuty vyhodnotí plán a zavolá `script.nabijeni_on` nebo `script.nabijeni_off`
- **15minutová optimalizace** - Vypočítává 96-slotový plán nabíjení s přesným řízením
- **Inteligentní režimy** - solar_charge, grid_charge_cheap, grid_charge_optimal, battery_discharge
- **Diagnostika** - Kompletní přehled stavu, konfigurace a logiky v diagnostickém senzoru
- **ApexCharts ready** - Všechny series senzory s atributy data_15min a timestamps pro grafy

## Nové v 1.4.0
✅ Aktivní automatizace - integrace sama volá nabíjecí skripty  
✅ Update každé 2 minuty místo 5 minut  
✅ Diagnostický senzor s kompletním přehledem  
✅ Lepší logování a monitoring  

## Instalace přes HACS
1. HACS → Settings → Custom repositories → Add repository  
   - Repository URL: `https://github.com/someone11221/gw_smart_energy_charging`
   - Category: Integration
2. Po instalaci restartujte Home Assistant
3. Settings → Devices & Services → Add Integration → GW Smart Charging

## Konfigurace (UI)
Všechny parametry lze nastavit přes UI:
- **Senzory**: forecast, price, load, daily_load, SOC, battery_power, grid_import
- **Skripty**: `script.nabijeni_on`, `script.nabijeni_off` (automaticky volány)
- **Baterie**: capacity (17 kWh), max_charge_power (3.7 kW), efficiency (0.95)
- **SOC**: min (10%), max (95%), target (90%)
- **Ceny**: always_charge_price (1.5), never_charge_price (4.0), hysteresis (5%)
- **Critical hours**: start (17), end (21), SOC (80%)
- **Automatizace**: enable_automation (true)

## Senzory
- `sensor.gw_smart_charging_forecast_status` - Stav integrace
- `sensor.gw_smart_charging_forecast` - PV forecast s atributy
- `sensor.gw_smart_charging_price` - Ceny s atributy
- `sensor.gw_smart_charging_schedule` - Aktuální režim a plán
- `sensor.gw_smart_charging_soc_forecast` - Predikce SOC
- `sensor.gw_smart_charging_diagnostics` - 🆕 Kompletní diagnostika
- `switch.gw_smart_charging_auto_charging` - Switch pro manuální ovládání
- **Series senzory** (pro grafy): pv, load, battery_charge, battery_discharge, grid_import, soc_forecast

## ApexCharts příklad
```yaml
type: custom:apexcharts-card
header:
  show: true
  title: GW Smart Charging Plan
graph_span: 24h
span:
  start: day
series:
  - entity: sensor.gw_smart_charging_series_pv
    name: Solar Production
    type: area
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  - entity: sensor.gw_smart_charging_series_load
    name: House Load
    type: line
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  - entity: sensor.gw_smart_charging_series_battery_charge
    name: Battery Charge
    type: column
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  - entity: sensor.gw_smart_charging_series_soc_forecast
    name: SOC Forecast
    type: line
    yaxis_id: soc
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
yaxis:
  - id: power
    decimals: 1
    apex_config:
      title:
        text: Power (kW)
  - id: soc
    opposite: true
    decimals: 0
    apex_config:
      title:
        text: SOC (%)
```

## Ladění
Debug logování v `configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.gw_smart_charging: debug
```

## Podpora
- Issues: https://github.com/someone11221/gw_smart_energy_charging/issues
