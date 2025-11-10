# Release Notes

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