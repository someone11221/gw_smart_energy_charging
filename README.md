# GW Smart Charging

Pokročilá integrace pro Home Assistant optimalizující nabíjení baterie GoodWe pomocí solárního forecastu a cen elektřiny. **Verze 1.1.1** přináší 15minutové intervaly pro maximální přesnost řízení.

## Funkce

✨ **15minutová optimalizace** - Přesné řízení v 96 intervalech/den  
🌞 **Inteligentní self-consumption** - Priorita využití solárního přebytku  
💰 **Cenové prahové hodnoty** - Always/Never charge prahy  
🔋 **SOC limity** - Min/Max/Target pro ochranu baterie  
📊 **Predikce spotřeby** - Využití historických dat  
🤖 **Automatické ovládání** - Switch pro řízení podle plánu  

## Instalace

1. Add repository to HACS (type: Integration):  
   `https://github.com/someone11221/gw_smart_energy_charging`
2. Install via HACS → Integrations
3. Restart Home Assistant
4. Add integration through Settings → Devices & Services → Add Integration → GW Smart Charging

## Konfigurace

Integrace podporuje následující senzory:
- `sensor.energy_production_d2` - 15min PV forecast (watts attribute)
- `sensor.current_consumption_price_czk_kwh` - Ceny elektřiny (today/tomorrow_hourly_prices)
- `sensor.house_consumption` - Aktuální spotřeba (W)
- `sensor.house_consumption_daily` - Denní spotřeba (kWh)
- `sensor.battery_state_of_charge` - SOC baterie (%)
- `switch.nabijeni_ze_site` - Switch pro ovládání nabíjení

Parametry včetně cenových prahů a SOC limitů lze nastavit přes UI.

## Dokumentace

Detailní dokumentace je v `/custom_components/gw_smart_charging/README.md`

## Release Notes

### v1.1.1
- ✨ 15minutové intervaly (96 slotů/den) místo hodinových
- 🎯 Cenové prahy: always_charge_price, never_charge_price
- 🔋 SOC limity: min/max/target pro ochranu baterie
- 📊 Nové senzory: Schedule, SOC Forecast, Series soc_forecast
- 🔄 Switch pro automatické řízení nabíjení
- 📈 Predikce spotřeby z daily load sensor
- 📝 Kompletní dokumentace včetně Lovelace příkladů

### v1.0.x
- Základní optimalizace nabíjení
- Hodinové plánování
- UI konfigurace
