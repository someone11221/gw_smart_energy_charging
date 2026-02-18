# ⚡ Smart Battery Charging Controller for Home Assistant

[![hacs_badge](https://img.shields.io/badge/HACS-Custom-orange.svg)](https://github.com/hacs/integration)
[![version](https://img.shields.io/badge/version-3.2.0-blue.svg)](https://github.com/someone11221/gw_smart_energy_charging/releases)
[![license](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Inteligentní řízení nabíjení domácí baterie s optimalizací na **české spotové ceny elektřiny**. Integrace automaticky nakupuje energii v nejlevnějších hodinách, respektuje distribuční tarify (EG.D / ČEZ / PRE) a HDO signál.

<p align="center">
  <img src="docs/dashboard.png" alt="Dashboard" width="800">
</p>

## ✨ Funkce

- **Cenová optimalizace** — OTE / Nanogreen spotové ceny, 15-min plánovací intervaly, automatická detekce cenových peaků
- **Distribuční tarify ČR** — EG.D (E.ON), ČEZ Distribuce, PREdistribuce · 9 tarifů (D01d–D61d) · regulované poplatky ERÚ 2025
- **HDO signál** — čtení reálného NT/VT stavu ze senzoru v HA (výchozí `sensor.egdtar`)
- **Predikce spotřeby** — adaptivní učení z historie nebo fixní profil · auto-detekce z HA Energy Dashboard
- **Statistiky nákladů** — dnes/týden/měsíc/rok · průměrná cena · NT/VT podíl · odhad úspory oproti paušálu
- **Nouzový fallback** — automatický nouzový nabíjecí režim při výpadku cenových dat (>2h bez dat → noční nabíjení)
- **Debug systém** — ring buffer 500 eventů, filtrování, stažení logu z dashboardu jako TXT/JSON
- **Validace konfigurace** — ověření existence senzorů a skriptů přímo při nastavování integrace
- **Lovelace karta** — automaticky deploynutá, SOC/ceny/plán/statistiky/ovládání
- **Webový dashboard** — standalone na `/api/gw_smart_charging/dashboard` s grafy, statistikami, timeline

## 📦 Instalace

### HACS (doporučeno)

1. V HACS klikněte **⋮ → Vlastní repozitáře**
2. Přidejte `https://github.com/someone11221/gw_smart_energy_charging` jako **Integrace**
3. Nainstalujte **Smart Battery Charging Controller**
4. Restartujte Home Assistant
5. Přidejte integraci: **Nastavení → Zařízení a služby → Přidat integraci → Smart Battery Charging**

### Ruční instalace

1. Stáhněte [nejnovější release](https://github.com/someone11221/gw_smart_energy_charging/releases)
2. Rozbalte `custom_components/gw_smart_charging/` do `config/custom_components/`
3. Restartujte Home Assistant
4. Přidejte integraci přes UI

### Lovelace karta

Karta se automaticky nakopíruje do `/config/www/` a zaregistruje jako Lovelace resource. Stačí přidat na dashboard:

```yaml
type: custom:smart-charging-card
```

> Pokud používáte YAML mode dashboard, přidejte resource ručně: **Nastavení → Dashboardy → ⋮ → Zdroje** → URL: `/local/smart-charging-card.js`, Typ: JavaScript modul

## ⚙️ Konfigurace

Integrace se konfiguruje přes HA UI ve 4 krocích:

### 1. Cenový provider
| Parametr | Popis | Výchozí |
|----------|-------|---------|
| `price_provider` | OTE / Nanogreen | `ote` |
| `price_sensor` | Entity ID cenového senzoru | `sensor.current_consumption_price_czk_kwh` |

### 2. Distribuce & HDO
| Parametr | Popis | Výchozí |
|----------|-------|---------|
| `distributor` | EG.D / ČEZ / PRE | `egd` |
| `tariff` | Distribuční tarif (D01d–D61d) | `d57d` |
| `circuit_breaker` | Jistič (1x10A–3x80A) | `3x25A` |
| `hdo_sensor` | HDO senzor (on=NT) | `sensor.egdtar` |

### 3. Baterie & spotřeba
| Parametr | Popis | Výchozí |
|----------|-------|---------|
| `soc_sensor` | Senzor SOC baterie | `sensor.battery_state_of_charge` |
| `battery_power_sensor` | Senzor výkonu baterie | `sensor.battery_power` |
| `battery_capacity` | Kapacita baterie (kWh) | `17.0` |
| `charging_script_on` | Skript pro zapnutí nabíjení | `script.nabijeni_on` |
| `charging_script_off` | Skript pro vypnutí nabíjení | `script.nabijeni_off` |
| `prediction_mode` | Fixní / Adaptivní | `adaptive` |

### 4. Strategie
| Parametr | Popis | Výchozí |
|----------|-------|---------|
| `min_soc_before_peak` | Min. SOC před cenovým peakem | `80%` |
| `target_soc_full` | Cílové nabití | `95%` |
| `min_soc_safety` | Safety minimum | `20%` |
| `charging_power` | Nabíjecí výkon (kW) | `5.0` |
| `flat_price_compare` | Paušální cena pro odhad úspory (CZK/kWh) | `4.5` |

> Při zadávání senzorů se v reálném čase ověřuje existence entity, datový typ a dostupnost.

## 📊 Senzory (7)

| Senzor | Typ | Popis |
|--------|-----|-------|
| **Battery SOC** | `%` | Stav nabití + atributy: power, capacity, charging state |
| **Battery Power** | `W` | Aktuální výkon baterie (kladný=vybíjí, záporný=nabíjí) |
| **Electricity Price** | `CZK/kWh` | Spotová cena + atributy: HDO stav, VT/NT sazby, distribuce |
| **Charging Plan** | `slots` | Počet slotů + atributy: náklady dnes/týden/měsíc, detail slotů |
| **Next Charging** | `datetime` | Čas příštího nabíjení + atributy: hodiny do startu, cena, priorita |
| **Consumption Forecast** | `kWh` | Předpověď spotřeby 24h + atributy: mód predikce, zdroj dat |
| **Diagnostics** | `text` | Stav integrace (ok/charging/fallback/errors) + kompletní diagnostika |

> Náklady (dnes/týden/měsíc/rok), HDO stav a statistiky jsou v **atributech** existujících senzorů — ne jako samostatné entity.

## 🛠️ API Endpointy

| Endpoint | Metoda | Popis |
|----------|--------|-------|
| `/api/gw_smart_charging/dashboard` | GET | Webový dashboard (HTML) |
| `/api/gw_smart_charging/data` | GET | Kompletní JSON data |
| `/api/gw_smart_charging/statistics` | GET | Statistiky nákladů |
| `/api/gw_smart_charging/debug` | GET | Debug log (JSON, filtry: `?level=error&category=prices`) |
| `/api/gw_smart_charging/debug/download` | GET | Stažení logu (`?format=txt` nebo `json`) |
| `/api/gw_smart_charging/auto/{on\|off}` | POST | Zapnutí/vypnutí auto nabíjení |
| `/api/gw_smart_charging/refresh` | POST | Přepočítání nabíjecího plánu |
| `/api/gw_smart_charging/config` | POST | Aktualizace nastavení spotřeby |

## 🐛 Debugging

Integrace obsahuje vestavěný debug systém (ring buffer posledních 500 eventů):

1. Otevřete dashboard → sekce **🐛 Debug log** → klikněte **Zobrazit**
2. Filtrujte podle úrovně (Error/Warn/Action) a kategorie (prices/battery/hdo/plan/charging)
3. Stáhněte kompletní log: tlačítko **📥 TXT** nebo **📥 JSON**

Kategorie eventů:
- `prices` — aktualizace cen, OTE senzor
- `battery` — stav baterie, SOC, výkon
- `hdo` — HDO signál, NT/VT detekce
- `plan` — vytvoření a aktualizace nabíjecího plánu
- `charging` — start/stop nabíjení, rozhodovací logika
- `fallback` — nouzový režim při výpadku dat
- `config` — změny nastavení
- `stats` — statistiky a persistence

## 🔌 Nouzový fallback

Pokud OTE senzor neodpovídá déle než **2 hodiny**:
- Aktivuje se nouzový nabíjecí režim
- Nabíjecí okna: **01:00–05:00** a **13:00–15:00** (typické NT hodiny)
- Nabíjí pouze pokud SOC < 90%
- Dashboard zobrazí červený badge **⚠️ FALLBACK**
- Diagnostics senzor přejde do stavu `fallback`
- Po obnovení cenových dat se fallback automaticky deaktivuje

## 📋 Changelog

### v3.2.0 (2026-02-18)
- ✅ HDO signál ze senzoru v HA (real-time NT/VT)
- ✅ Adaptivní / fixní predikce spotřeby s exponenciálním váhováním
- ✅ Lovelace karta s automatickým deployem
- ✅ Auto-detekce z HA Energy Dashboard
- ✅ Persistentní statistiky nákladů (dnes/týden/měsíc/rok)
- ✅ Debug logger s ring bufferem a stahováním z dashboardu
- ✅ Nouzový fallback při výpadku cenových dat
- ✅ Validace senzorů a skriptů v config flow
- ✅ Konfigurovatelná paušální cena pro odhad úspory
- ✅ Redukce na 7 senzorů (náklady/HDO v atributech)
- ✅ Automatický cleanup starých entit z předchozích verzí
- ✅ Tooltipy v dashboardu s popisem každé metriky

### v3.1.0 (2026-02-18)
- Cenový graf jako hero dashboard
- SOC predikce z backendu
- Oprava UTC timezone bugu

### v3.0.9 (2026-02-17)
- Distribuční tarify ČR (EG.D/ČEZ/PRE)
- 15-minutové plánovací intervaly
- Consumption predictor z HA recorder
- HACS kompatibilita

## 📄 Licence

[MIT License](LICENSE) © 2025 Martin Rak
