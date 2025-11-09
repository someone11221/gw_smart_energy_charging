# GW Smart Charging

Integrace propojuje GoodWe (goodwe integration) se solárním forecastem a cenami elektřiny a optimalizuje nabíjení baterie tak, aby minimalizovala náklady a maximalizovala využití vlastní FVE.

Co dělá
- Vypočítává 24-hodinový plán nabíjení (mode: pv / grid / idle) a vystavuje jej v sensoru.
- Podporuje UI config flow (přidání přes Settings → Devices & Services → Add integration).
- Nabízí služby:
  - gw_smart_charging.optimize_now
  - gw_smart_charging.apply_schedule_now

Instalace přes HACS
1. HACS → Settings → Custom repositories → Add repository  
   - Repository URL: https://github.com/someone11221/gw_smart_energy_charging  
   - Category: Integration
2. Po instalaci restartujte Home Assistant.
3. Settings → Devices & Services → Add Integration → GW Smart Charging

Konfigurace (UI)
- forecast_sensor: sensor s 24hodinovou předpovědí PV
- price_sensor: sensor s 24hodinovými cenami elektřiny
- pv_power_sensor (volitelně): aktuální výkon FVE
- soc_sensor: sensor stavu nabití baterie (SOC)
- goodwe_switch: switch pro povolení/zakázání nabíjení ze sítě
- battery_capacity_kwh, max_charge_power_kw, charge_efficiency, min_reserve_pct
