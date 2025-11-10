# GW Smart Charging

Pokročilá integrace pro Home Assistant optimalizující nabíjení baterie GoodWe pomocí solárního forecastu a cen elektřiny. **Verze 1.4.0** - automatické řízení nabíjení každé 2 minuty s real-time reakcí na změny.

## Funkce

✨ **Automatické řízení** - Aktivní ovládání nabíjení každé 2 minuty  
🎯 **15minutová optimalizace** - Přesné řízení v 96 intervalech/den  
🌞 **Inteligentní self-consumption** - Priorita využití solárního přebytku  
💰 **Cenové prahové hodnoty** - Always/Never charge prahy s hysterezí  
🔋 **SOC limity** - Min/Max/Target pro ochranu baterie  
📊 **ML Predikce spotřeby** - Učení z historických dat (30 dní)  
⚡ **Critical Hours** - Vyšší SOC během peak hours  
🤖 **Script automation** - Automatické volání script.nabijeni_on/off  
📈 **Real-time monitoring** - Battery power & grid import  
🔍 **Diagnostika** - Kompletní přehled stavu a logiky integrace  

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
- `sensor.battery_power` - Real-time nabíjecí/vybíjecí výkon
- `sensor.energy_buy` - Grid import monitoring
- `sensor.battery_state_of_charge` - SOC baterie (%)
- `script.nabijeni_on` - Script pro zapnutí nabíjení
- `script.nabijeni_off` - Script pro vypnutí nabíjení

Parametry včetně cenových prahů, SOC limitů, hystereze a critical hours lze nastavit přes UI.

## Dokumentace

Detailní dokumentace je v `/custom_components/gw_smart_charging/README.md`

## Release Notes

### v1.4.0 (Active Automation Release)
- ✅ **Automatické řízení** - Integrace aktivně volá script.nabijeni_on/off každé 2 minuty
- 🔄 **Vyšší frekvence aktualizací** - Update interval snížen z 5 na 2 minuty pro rychlejší reakci
- 🎯 **Chytrá optimalizace** - Skripty se volají pouze při změně stavu (prevence zbytečných volání)
- 🔍 **Nový diagnostický senzor** - Kompletní přehled stavu, konfigurace a logiky integrace
- 📊 **Vylepšená data pro ApexCharts** - Optimalizovaný formát atributů pro grafování
- 📋 **Detailní logování** - Přesné informace o volání skriptů a režimech nabíjení
- 🔧 **Stabilní konfigurace** - Všechny senzory a skripty správně propojené

### v1.3.0 (Production Release)
- ✅ **Production Ready** - Kompletně otestovaná a stabilní verze
- 🔧 **Defaultní konfigurace** - Všechny senzory mají správné výchozí hodnoty
- 📋 **Kompletní dokumentace** - Mapování senzorů pro snadnou instalaci
- 🎯 **Optimalizovaná logika** - Hystereze, ML predikce, Critical hours
- 🔒 **Security** - 0 vulnerabilities (CodeQL verified)

### v1.2.0
- 🔄 **Hystereze** - ±5% buffer kolem cenových prahů pro prevenci oscilace
- 🧠 **ML Predikce** - Průměrování 30 denních vzorů spotřeby pro přesnější plánování
- ⏰ **Critical Hours** - Udržování vyššího SOC během peak hours (default 17-21)
- 📊 **Nové senzory** - battery_power, energy_buy (grid import)
- 🎯 **Smart režimy** - grid_charge_critical pro rozlišení peak hour charging

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
