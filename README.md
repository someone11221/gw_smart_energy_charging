# GW Smart Charging

Pokročilá integrace pro Home Assistant optimalizující nabíjení baterie GoodWe pomocí solárního forecastu a cen elektřiny. **Verze 1.7.0** - autonomní služba s denními statistikami, predikcemi a funkčním ApexCharts dashboardem.

## Funkce

✨ **Automatické autonomní řízení** - Aktivní ovládání nabíjení každé 2 minuty bez zásahu uživatele  
🎯 **15minutová optimalizace** - Přesné řízení v 96 intervalech/den  
🌞 **Inteligentní self-consumption** - Priorita využití solárního přebytku  
💰 **Cenové prahové hodnoty** - Always/Never charge prahy s hysterezí  
🔋 **SOC limity** - Min/Max/Target pro ochranu baterie  
📊 **Denní statistiky** - Plánované vs skutečné nabíjení, úspory, efektivita  
🔮 **Vylepšená ML Predikce** - Vážené průměrování z 30 dní historických dat s quality score  
⚡ **Critical Hours** - Vyšší SOC během peak hours  
🤖 **Script automation** - Automatické volání script.nabijeni_on/off  
📈 **Real-time monitoring** - Battery power & grid import  
🔍 **Diagnostika** - Kompletní přehled stavu a logiky integrace  
🔄 **W→kWh konverze** - Automatický převod jednotek pro správnou logiku  
📉 **Sledování nabíjení/vybíjení** - Today's charge/discharge tracking  
🎨 **Funkční ApexCharts Dashboard** - Grafy optimalizace s data_generator pro v1.7.0  
🛠️ **Služba pro automatizace** - `get_charging_schedule` s detailními údaji  
📝 **Activity log** - Sledování změn režimů a stavu systému  
💡 **Prediction sensor** - Konfidence ML a forecastu, kvalita predikce  
💸 **Savings tracking** - Úspory oproti pausálnímu tarifu  

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

## Nové v1.6.0

### Služba pro automatizace
Nová služba `gw_smart_charging.get_charging_schedule` poskytuje detailní informace o plánu nabíjení:
- Plánované periody nabíjení ze sítě
- Plánované periody vybíjení baterie
- Plánované periody nabíjení ze solárů
- Sloty s očekávaným importem ze sítě
- Denní statistiky (kWh, náklady)
- Real-time metriky baterie a sítě
- Informace o optimalizaci

### Nové senzory
- `sensor.gw_smart_charging_next_grid_charge` - Čas příštího nabíjení ze sítě
- `sensor.gw_smart_charging_next_battery_discharge` - Čas příštího vybíjení baterie
- `sensor.gw_smart_charging_activity_log` - Log změn režimů a aktivit

### Vylepšená optimalizace
- **Vážená ML predikce**: Novější dny mají větší vliv na predikci spotřeby
- **Chytřejší grid charging**: Rozhodování založené na budoucím deficitu energie
- **Respektování kapacity baterie**: Prevence přebíjení a zbytečných cyklů
- **Minimální prah nabíjení**: Nabíjí pouze pokud je potřeba > 0.5 kWh

Více informací v `FEATURE_SERVICE_v1.6.0.md`.

## Dokumentace

Detailní dokumentace je v `/custom_components/gw_smart_charging/README.md`

## Release Notes

### v1.7.0 (Autonomous Service & Statistics Release)
- 🤖 **Autonomní služba** - Integrace funguje plně autonomně bez zásahu uživatele
- 📊 **Nový sensor: Daily Statistics** - Denní statistiky nabíjení, úspory, efektivita
- 🔮 **Nový sensor: Prediction** - ML konfidence, kvalita predikce, forecast confidence
- 💸 **Savings tracking** - Výpočet úspor oproti pausálnímu tarifu
- 📈 **Funkční ApexCharts** - Opraven data_generator pro správné zobrazení grafů
- 🎨 **Nový Lovelace dashboard** - Kompletní dashboard s všemi novými senzory (lovelace_v1.7.0.yaml)
- 📋 **Efektivita nabíjení** - Porovnání plánovaného vs skutečného nabíjení
- 🔍 **Prediction quality score** - Celkový score kvality predikce (0-100)
- 📝 **Rozšířené senzory** - Všechny senzory zobrazují podrobné stavy a atributy
- ✨ **Ready for release** - Připraveno pro produkční nasazení

### v1.6.0 (Service & Enhanced Optimization Release)
- 🛠️ **Nová služba** - `get_charging_schedule` pro automatizace, skripty a scény
- 📝 **3 nové senzory** - next_grid_charge, next_battery_discharge, activity_log
- 🧠 **Vylepšená ML predikce** - Vážené průměrování s exponenciálním rozpadem
- 🔮 **Chytrá optimalizace** - Rozhodování založené na budoucí spotřebě a kapacitě baterie
- 📊 **Activity tracking** - Sledování změn režimů a stavu systému
- 📋 **Rozšířené příklady** - Nové automatizace využívající službu
- 🔧 **Lepší grid charging** - Výpočet energy deficitu pro optimální nabíjení

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
