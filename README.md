# GW Smart Charging

Pokročilá integrace pro Home Assistant optimalizující nabíjení baterie GoodWe pomocí solárního forecastu a cen elektřiny. **Verze 1.5.0** - automatické řízení nabíjení každé 2 minuty s real-time reakcí na změny, W→kWh konverze a dashboard.

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
🔄 **W→kWh konverze** - Automatický převod jednotek pro správnou logiku  
📉 **Sledování nabíjení/vybíjení** - Today's charge/discharge tracking  
🎨 **Dashboard** - Přehledný dashboard podobný open-meteo integraci  

## Instalace

1. Add repository to HACS (type: Integration):  
   `https://github.com/someone11221/gw_smart_energy_charging`
2. Install via HACS → Integrations
3. Restart Home Assistant
4. Add integration through Settings → Devices & Services → Add Integration → GW Smart Charging
5. Access dashboard at: `/api/gw_smart_charging/dashboard`

## Konfigurace

Integrace podporuje následující senzory:
- `sensor.energy_production_d2` - 15min PV forecast (watts attribute) → automaticky převedeno na kWh
- `sensor.current_consumption_price_czk_kwh` - Ceny elektřiny (today/tomorrow_hourly_prices)
- `sensor.house_consumption` - Aktuální spotřeba (W) → automaticky převedeno na kWh
- `sensor.house_consumption_daily` - Denní spotřeba (kWh)
- `sensor.battery_power` - Real-time nabíjecí/vybíjecí výkon (W, **kladné hodnoty = vybíjení, záporné = nabíjení**)
- `sensor.energy_buy` - Grid import monitoring (W) → automaticky převedeno na kWh
- `sensor.battery_state_of_charge` - SOC baterie (%), kapacita 17 kWh
- `sensor.today_battery_charge` - Kolik kWh bylo dnes do baterie uloženo
- `sensor.today_battery_discharge` - Kolik kWh bylo dnes z baterie odebráno
- `sensor.pv_power` - Aktuální výroba solárních panelů (W) → automaticky převedeno na kWh
- `script.nabijeni_on` - Script pro zapnutí nabíjení
- `script.nabijeni_off` - Script pro vypnutí nabíjení

**Důležité:** Všechny výkonové senzory (W) jsou automaticky převáděny na kWh pro správnou logiku integrace.

Parametry včetně cenových prahů, SOC limitů, hystereze a critical hours lze nastavit přes UI.

## Dashboard

Integrace poskytuje přehledný dashboard podobný open-meteo integraci:
- Zobrazení všech senzorů z integrace
- Výpis aktivity integrace
- Statistiky a diagnostika
- Real-time monitoring baterie a sítě

Dashboard je dostupný na: `/api/gw_smart_charging/dashboard`

## Dokumentace

Detailní dokumentace je v `/custom_components/gw_smart_charging/README.md`

## Release Notes

### v1.5.0 (Unit Conversion & Dashboard Release)
- 🔄 **W→kWh konverze** - Automatický převod výkonových senzorů (W) na energii (kWh) pro správnou logiku
- 📊 **Battery power sign handling** - Správné zpracování sensor.battery_power (+ = vybíjení, - = nabíjení)
- 📉 **Nové senzory** - Today's battery charge/discharge tracking v kWh
- 🎨 **Dashboard** - Nový přehledný dashboard podobný open-meteo integraci
- 📈 **Real-time metriky** - Rozšířená diagnostika s battery a grid metrikami v W i kWh
- 🔧 **Vylepšená konfigurace** - Podpora pro sensor.today_battery_charge a sensor.today_battery_discharge
- 📝 **Strings.json** - Přidány překlady pro lepší UI
- ✨ **Vylepšený diagnostický senzor** - Kompletní přehled včetně real-time battery status

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
