# Release Notes

## v1.5.0 - Unit Conversion & Dashboard Release (November 2024)

### 🎯 Major Features
- **W→kWh konverze** - Automatický převod všech výkonových senzorů (W) na energii (kWh) pro správnou logiku
- **Battery power sign handling** - Správné zpracování `sensor.battery_power` kde **kladné hodnoty = vybíjení**, **záporné = nabíjení**
- **Dashboard** - Nový přehledný dashboard podobný open-meteo integraci, dostupný na `/api/gw_smart_charging/dashboard`
- **Real-time battery & grid metriky** - Rozšířené sledování baterie a sítě s W i kWh jednotkami

### 🔍 New Sensors
- **Battery Power Sensor** - `sensor.gw_smart_charging_battery_power` - Real-time výkon baterie v W (+ = vybíjení, - = nabíjení)
- **Today Battery Charge** - `sensor.gw_smart_charging_today_battery_charge` - Kolik kWh bylo dnes do baterie uloženo
- **Today Battery Discharge** - `sensor.gw_smart_charging_today_battery_discharge` - Kolik kWh bylo dnes z baterie odebráno

### 📊 Improvements
- **Vylepšený diagnostický senzor** - Rozšířené atributy s real-time metrikami:
  - Battery power v W a kW
  - Battery status (charging/discharging/idle)
  - Battery SOC v % a kWh
  - Today's charge/discharge v kWh
  - Grid import v W a kW
  - House load v W a kW
  - PV power v W a kW
- **Strings.json** - Přidány české i anglické překlady pro lepší UI
- **Unit conversions** - Všechny power senzory (W) automaticky převáděny na kWh pro logiku:
  - `sensor.pv_power` (W) → kW v logice
  - `sensor.house_consumption` (W) → kW v logice
  - `sensor.energy_buy` (W) → kW v logice
  - `sensor.battery_power` (W) → kW v logice s správným znaménkem

### 🎨 Dashboard Features
Dashboard (`/api/gw_smart_charging/dashboard`) obsahuje:
- Statistiky senzorů a switches
- Přehled všech funkcí integrace
- Seznam všech dostupných senzorů
- Konfigurace a nastavení
- Real-time status integrace
- Krásné responzivní UI s gradientem

### 🔧 Configuration
- Nové config fieldy:
  - `today_battery_charge_sensor` - Sensor pro today's charge (default: `sensor.today_battery_charge`)
  - `today_battery_discharge_sensor` - Sensor pro today's discharge (default: `sensor.today_battery_discharge`)
- Všechny config fieldy mají defaults pro snadnou konfiguraci

### 📝 Documentation Updates
- README.md aktualizován na v1.5.0
- Zdůrazněno W→kWh konverze
- Vysvětleno battery_power sign (+ = vybíjení, - = nabíjení)
- Přidán odkaz na dashboard
- Rozšířen seznam senzorů

### 🔄 Technical Details
- Nové helper metody v coordinator:
  - `_get_battery_metrics()` - Získá real-time battery metriky s konverzemi
  - `_get_grid_metrics()` - Získá real-time grid metriky s konverzemi
- Dashboard view registrována v `__init__.py`
- Nový `view.py` modul pro dashboard HTML
- Všechny power hodnoty správně převáděny: `value_w / 1000.0 = value_kw`

### 💡 Further Improvements Suggested
1. **Grafy v dashboardu** - Přidat ApexCharts nebo plotly grafy pro vizualizaci
2. **History tracking** - Ukládat historii nabíjení/vybíjení pro dlouhodobou analýzu
3. **Notifications** - Upozornění při nízkém SOC nebo vysokých cenách
4. **Adaptive learning** - Rozšířit ML predikci o detekci víkendů a svátků
5. **Export dat** - Možnost exportu dat do CSV/JSON
6. **Mobile optimalizace** - Responsive design dashboardu pro mobily
7. **Dark mode** - Podpora dark mode v dashboardu
8. **API endpoints** - REST API pro externí přístup k datům

---

## v1.4.0 - Active Automation Release (November 2024)

### 🎯 Major Features
- **Automatické řízení nabíjení** - Integrace nyní aktivně volá `script.nabijeni_on` a `script.nabijeni_off` každé 2 minuty na základě optimalizovaného plánu
- **Vyšší frekvence aktualizací** - Update interval snížen z 5 na 2 minuty pro rychlejší reakci na změny cen a forecastu
- **Inteligentní volání skriptů** - Skripty se volají pouze při změně stavu, ne opakovaně (prevence zbytečného zatížení)

### 🔍 New Sensors
- **Diagnostics sensor** - Nový senzor `sensor.gw_smart_charging_diagnostics` poskytuje kompletní přehled:
  - Aktuální stav automatizace a poslední volání skriptu
  - Distribuci režimů nabíjení v denním plánu
  - Čas a cenu příštího období nabíjení
  - Konfiguraci všech senzorů a skriptů
  - Forecast confidence a metadata

### 📊 Improvements
- **Lepší logování** - Detailní záznamy o volání skriptů včetně slotu, režimu a ceny
- **Optimalizovaná data** - Vylepšený formát atributů pro ApexCharts a jiné vizualizační nástroje
- **Dokumentace** - Rozšířená dokumentace s popisem automatizace a diagnostiky

### 🔧 Configuration
- Všechny defaultní hodnoty správně nastavené pro běžné použití
- Podpora rekonfigurace přes UI bez restartu HA
- Enable/disable automation přes config

### 📝 Documentation Updates
- README.md aktualizován na v1.4.0
- Detailní popis fungování automatizace
- Příklady použití diagnostického senzoru

---

## v1.3.0 - Production Release

### Features
- Production ready s kompletním testováním
- Hystereze pro prevenci oscilace nabíjení
- ML predikce spotřeby z historických dat
- Critical hours pro vyšší SOC během peak hours
- Security audit s 0 vulnerabilities

---

## v1.0.0 - Initial HACS Release

### Features
- Initial release s podporou HACS
- 15minutová optimalizace nabíjení
- Cenové prahy a SOC limity
- Základní senzory a vizualizace