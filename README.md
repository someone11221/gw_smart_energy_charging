# GW Smart Charging

GW Smart Charging automatizuje nabíjení baterie přes GoodWe invertor podle solárního forecastu a hodinových cen elektřiny.

Funkce
- Vypočítává 24-hodinový plán nabíjení (mode: pv/grid/idle) a vystavuje jej v sensoru.
- Podpora HA config flow (přidání přes UI).
- Služby: gw_smart_charging.optimize_now a gw_smart_charging.apply_schedule_now.
- HACS-ready (hacs.json, info.md, release).

Kompatibilita
- Minimální Home Assistant: 2025.1.0
- Verze této integrace: 1.0.0

Instalace přes HACS
1. V Home Assistant → HACS → Settings → Custom repositories → Add repository
   - Repository URL: https://github.com/someone11221/gw_smart_energy_charging
   - Category: Integration
2. Po instalaci restartuj Home Assistant.
3. Settings → Devices & Services → Add Integration → GW Smart Charging

Konfigurace (UI)
- forecast_sensor: senzor s 24hodinovou předpovědí (např. ha-open-meteo-solar-forecast)
- price_sensor: senzor s 24hodinovými cenami
- soc_sensor: sensor.battery_state_of_charge
- goodwe_switch: switch.nabijeni_ze_site (default)
- battery_capacity_kwh: 17 (default)
- min_reserve_pct: 10 (default)

Ladění
- Pro ladění zapněte logování (configuration.yaml):
```
logger:
  default: warning
  logs:
    custom_components.gw_smart_charging: debug
    homeassistant.config_entries: debug
```

Podpora
- Issue tracker: https://github.com/someone11221/gw_smart_energy_charging/issues

Licence
- MIT
