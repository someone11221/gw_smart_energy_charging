# GW Smart Charging

Pokročilá integrace pro Home Assistant optimalizující nabíjení baterie GoodWe pomocí solárního forecastu a cen elektřiny. **Verze 1.9.0** - Custom Lovelace card, Options Flow a panel v postranní liště.

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
🔍 **Diagnostika** - Kompletní přehled stavu a logiky integrace s aktuálním SoC  
🔄 **W→kWh konverze** - Automatický převod jednotek pro správnou logiku  
📉 **Sledování nabíjení/vybíjení** - Today's charge/discharge tracking  
🛠️ **Služba pro automatizace** - `get_charging_schedule` s detailními údaji  
📝 **Activity log** - Sledování změn režimů a stavu systému  
💡 **Prediction sensor** - Konfidence ML a forecastu, kvalita predikce  
💸 **Savings tracking** - Úspory oproti pausálnímu tarifu  
📱 **Device Panel** - Kompletní integrace v Zařízení a Služby  
🎨 **Zjednodušené entity** - Pouze 9 základních senzorů + 1 switch  
🎴 **Custom Lovelace Card** - Profesionální karta s kompaktním přehledem (v1.9.0)  
⚙️ **Options Flow** - Rekonfigurace bez reinstalace (v1.9.0)  
🔲 **Panel v postranní liště** - Přímý přístup k dashboardu (v1.9.0)  

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

**NOVINKA v1.9.0**: Panel je nyní integrován přímo v postranní liště Home Assistentu! Klikněte na ikonu "GW Smart Charging" v menu pro přístup k dashboardu.

## Custom Lovelace Card (v1.9.0)

Integrace poskytuje vlastní Lovelace kartu pro kompaktní přehled všech klíčových metrik:

### Použití karty
```yaml
type: custom:gw-smart-charging-card
entity: sensor.gw_smart_charging_diagnostics
```

### Funkce karty
- ⚡ **Real-time SOC** - Vizuální gradient lišta (červená→žlutá→zelená)
- 📊 **Klíčové metriky** - Peak forecast, aktuální cena, plánované nabíjení, další nabíjení
- 🎨 **Barevné indikátory** - Režimy nabíjení s barvami (grid_charge, solar_charge, battery_discharge, self_consume)
- 🔄 **Integrovaný switch** - Ovládání automatického nabíjení přímo z karty
- 📱 **Responzivní design** - Funguje na desktop i mobile

Karta je automaticky registrována po instalaci integrace.

## Rekonfigurace (v1.9.0)

**Options Flow** umožňuje změnit konfiguraci bez reinstalace:

1. Přejděte na Nastavení → Zařízení a Služby
2. Najděte "GW Smart Charging"
3. Klikněte na **KONFIGURACE**
4. Změňte senzory nebo parametry
5. Uložte - integrace se automaticky reloadne

Žádná ztráta dat, žádná reinstalace!

## Senzory (v1.8.0)

Integrace poskytuje **9 základních senzorů** a **1 switch**:

### Hlavní senzory
1. **`sensor.gw_smart_charging_forecast`** - Solární forecast s cenami elektřiny
2. **`sensor.gw_smart_charging_schedule`** - Aktuální plán nabíjení
3. **`sensor.gw_smart_charging_soc_forecast`** - Předpověď SOC s daty pro grafy
4. **`sensor.gw_smart_charging_battery_power`** - Výkon baterie a dnešní součty

### Diagnostika a statistiky
5. **`sensor.gw_smart_charging_diagnostics`** - Diagnostika systému s aktuálním SoC
6. **`sensor.gw_smart_charging_daily_statistics`** - Denní statistiky a úspory
7. **`sensor.gw_smart_charging_prediction`** - Kvalita ML predikce

### Automatizace
8. **`sensor.gw_smart_charging_next_charge`** - Další plánované nabíjení/vybíjení
9. **`sensor.gw_smart_charging_activity_log`** - Historie aktivit

### Ovládání
10. **`switch.gw_smart_charging_auto_charging`** - Automatické řízení

**Poznámka:** Data z předchozích 11 senzorů (series, today charge/discharge, atd.) jsou nyní dostupná jako atributy konsolidovaných senzorů. Viz `RELEASE_NOTES_v1.8.0.md` pro detaily migrace.

## Dokumentace logiky nabíjení

Detailní dokumentace logiky nabíjení je v `/CHARGING_LOGIC.md`. Tento dokument obsahuje:
- Popis všech použitých senzorů a jejich účelu
- Krok za krokem proces rozhodování
- Příklady scénářů pro různé denní doby
- Vysvětlení všech režimů nabíjení
- Konfigurace parametrů

## Nové v1.9.0

### Custom Lovelace Card
- **Profesionální karta** s kompaktním přehledem všech metrik
- **Vizuální SOC lišta** s gradientem (červená→žlutá→zelená)
- **Klíčové metriky** na jednom místě
- **Barevné indikátory** režimů nabíjení
- **Integrovaný switch** pro ovládání

### Panel v Postranní Liště
- **Přímý přístup** k dashboardu z menu
- **Ikona baterie** v postranní liště
- **Dostupné všem uživatelům** (ne jen admin)

### Options Flow
- **Rekonfigurace bez reinstalace** - změňte senzory/parametry přes UI
- **Automatické reload** po změně
- **Žádná ztráta dat** při úpravě konfigurace
- Cesta: Nastavení → Zařízení a Služby → GW Smart Charging → KONFIGURACE

### Energy Dashboard Integrace
- **Proper device_class** na všech energetických senzorech
- **State_class** pro správné měření
- **Připraveno pro HA Energy Dashboard**

## Nové v1.8.0

### Device Panel Integrace
Integrace se nyní zobrazuje v panelu Zařízení a Služby:
- Všechny entity přístupné z jednoho místa
- Přehledná organizace senzorů a ovládání
- Snadná diagnostika a konfigurace

### Konsolidace entit
- **Zredukováno z 21 na 10 entit** - Jednodušší přehled
- **Série data** - Přesunuta do atributů `sensor.gw_smart_charging_soc_forecast`
- **Today's totals** - Dostupné v atributech `sensor.gw_smart_charging_battery_power`
- **Ceny** - Sloučeny do `sensor.gw_smart_charging_forecast`
- **Next periods** - Sloučeny do `sensor.gw_smart_charging_next_charge`

### Opravy
- **Diagnostika** - Nyní správně zobrazuje aktuální SoC ze `sensor.battery_state_of_charge`
- **Lepší pochopitelnost** - Jasné názvy a popisy senzorů

### Dokumentace
- **CHARGING_LOGIC.md** - Kompletní dokumentace logiky nabíjení
- **RELEASE_NOTES_v1.8.0.md** - Detailní release notes s migrační příručkou

## Release Notes

### v1.8.0 (Entity Consolidation & Device Integration Release)

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

### v1.8.0 (Entity Consolidation & Device Integration Release)
- 📱 **Device Panel** - Plná integrace do Zařízení a Služby v Home Assistentu
- 🎯 **Konsolidace entit** - Snížení z 21 na 10 entit pro lepší přehlednost
- 🔧 **Oprava diagnostiky** - Správné zobrazení aktuálního SoC v diagnostickém senzoru
- 📚 **Dokumentace logiky** - Nový soubor CHARGING_LOGIC.md s kompletním popisem
- 📊 **Série data v atributech** - Grafy dostupné v atributech `soc_forecast` senzoru
- 💡 **Lepší pochopitelnost** - Jasné názvy senzorů a jejich účel
- 🔄 **Migrace** - Data z odstraněných senzorů dostupná v konsolidovaných atributech
- ✨ **Device Info** - Všechny entity nyní mají device_info pro správné seskupení

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
