# GW Smart Charging v1.4.0 - Implementation Summary
# ==================================================

## ✅ COMPLETED CHANGES

### 1. Automatic Script Execution (HLAVNÍ ZMĚNA)
**Soubor:** `custom_components/gw_smart_charging/coordinator.py`

- **Update interval**: Změněn z 5 na 2 minuty (řádek 61)
- **Nová metoda**: `_execute_charging_automation()` (řádky 153-196)
  - Automaticky volá `script.nabijeni_on` nebo `script.nabijeni_off`
  - Volá skripty pouze při změně stavu (ne opakovaně)
  - Detailní logování každého volání
  - Kontrola `enable_automation` konfigurace
- **Tracking**: Přidán `_last_script_state` pro sledování stavu (řádek 71)
- **Volání**: Automatizace spuštěna v `_async_update_data()` (řádek 139)

### 2. Nový Diagnostický Senzor
**Soubor:** `custom_components/gw_smart_charging/sensor.py`

- **Třída**: `GWSmartDiagnosticsSensor` (řádky 217-282)
- **Zobrazuje**:
  - Aktuální stav automatizace a poslední volání skriptu
  - Distribuci režimů v denním plánu
  - Čas a cenu příštího nabíjení
  - Kompletní konfiguraci senzorů a skriptů
  - Forecast confidence a metadata
- **Entity ID**: `sensor.gw_smart_charging_diagnostics`

### 3. Aktualizované Verze
- `manifest.json`: version "1.4.0"
- Git tag: 1.4.0 vytvořen (je třeba push)

### 4. Vylepšená Dokumentace

#### README.md (hlavní)
- Aktualizován na v1.4.0
- Přidány nové features (automatizace, diagnostika)
- Nové release notes

#### custom_components/gw_smart_charging/README.md
- Sekce o automatizaci s detailním vysvětlením
- Popis diagnostického senzoru
- 4 komplexní ApexCharts příklady:
  1. Status card s diagnostikou
  2. Kompletní 24h plán (5 series)
  3. Graf cen s prahovými hodnotami
  4. Kompletní dashboard view

#### RELEASE_NOTES.md
- Detailní changelog pro v1.4.0
- Popis všech změn a vylepšení

#### info.md
- Aktualizován s příkladem ApexCharts
- Nové features zvýrazněny

### 5. Nové Příklady (examples/)

#### automations.yaml
7 příkladů automatizací:
1. Notifikace při změně režimu
2. Alert při grid nabíjení
3. Manuální vynucené nabíjení
4. Bezpečnostní zastavení při vysoké ceně
5. Ranní přehled plánu
6. Logování režimů
7. Disable/enable při údržbě

#### scripts.yaml
6 příkladů skriptů:
1. `nabijeni_on` - základní (s 3 variantami implementace)
2. `nabijeni_off` - základní (s 3 variantami implementace)
3. `nabijeni_on_advanced` - s podmínkami
4. `nabijeni_on_priority` - s nastavením priority
5. `test_gw_charging` - testovací script
6. `gw_emergency_stop` - nouzové zastavení

#### lovelace.yaml
Kompletní dashboard konfigurace:
1. Status card s diagnostikou
2. ApexCharts - 24h plán (všech 5 series)
3. ApexCharts - ceny s prahy
4. Konfigurace overview
5. Kompaktní karta
6. Mobile-friendly karta
7. Diagnostická karta

## 🎯 CO INTEGRACE NYNÍ DĚLÁ

### Automatický proces (každé 2 minuty):
1. **Aktualizace dat** - Načte forecast, ceny, spotřebu
2. **Výpočet plánu** - Vytvoří optimalizovaný 96-slotový plán
3. **Vyhodnocení** - Zjistí aktuální 15min slot a rozhodne
4. **Akce** - Zavolá `script.nabijeni_on` nebo `script.nabijeni_off`
5. **Logování** - Zaznamenává všechny akce do logu

### Rozhodovací logika:
- ✅ **Solar charge** - Pokud je solární přebytek
- ✅ **Grid charge cheap** - Cena ≤ always_charge_price (1.5 CZK)
- ✅ **Grid charge optimal** - Cena < never_charge_price (4.0 CZK) a baterie pod target
- ✅ **Grid charge critical** - Během critical hours (17-21) pro vyšší SOC
- ✅ **Battery discharge** - Vybíjení pro pokrytí spotřeby
- ⛔ **Never charge** - Cena > never_charge_price

### Hystereze (±5%):
- Předchází rychlému přepínání kolem cenových prahů
- Pokud nabíjí → těžší vypnout (vyšší práh)
- Pokud nenabíjí → těžší zapnout (nižší práh)

## 📊 NOVÉ SENZORY

### sensor.gw_smart_charging_diagnostics
**Atributy:**
- `automation_enabled` - Zda je automatizace zapnutá
- `charging_on_script` - Konfigurovaný ON script
- `charging_off_script` - Konfigurovaný OFF script
- `last_script_state` - Poslední stav volání (true/false/null)
- `current_slot` - Aktuální 15min slot (0-95)
- `current_mode` - Aktuální režim (solar_charge, grid_charge_cheap, atd.)
- `should_charge_now` - Mělo by se právě nabíjet
- `charging_slots_today` - Kolik slotů dnes nabíjí
- `next_charge_time` - Kdy další nabíjení (čas)
- `next_charge_price` - Cena příštího nabíjení
- `mode_distribution` - Počet slotů pro každý režim
- `forecast_confidence` - Kvalita forecastu
- `last_update` - Čas poslední aktualizace

## 🔧 CO JE TŘEBA UDĚLAT

### 1. Push Git Tag (MANUÁLNĚ)
```bash
git push origin 1.4.0
```

### 2. Instalace a Konfigurace

#### Nainstalovat integraci:
1. HACS → Custom repositories → Add
2. URL: https://github.com/someone11221/gw_smart_energy_charging
3. Category: Integration
4. Restart Home Assistant
5. Přidat integraci přes UI

#### Vytvořit nabíjecí skripty:
Zkopírovat z `examples/scripts.yaml` a přizpůsobit pro vaši GoodWe konfiguraci:
- `script.nabijeni_on` - musí zapnout nabíjení z gridu
- `script.nabijeni_off` - musí vypnout nabíjení z gridu

**Důležité:** Názvy scriptů musí odpovídat konfiguraci v integraci!

#### Nastavit senzory:
- `sensor.energy_production_d2` - 15min PV forecast
- `sensor.current_consumption_price_czk_kwh` - Ceny
- `sensor.house_consumption` - Aktuální spotřeba (W)
- `sensor.house_consumption_daily` - Denní spotřeba (kWh)
- `sensor.battery_state_of_charge` - SOC baterie (%)
- `sensor.battery_power` - Real-time battery power
- `sensor.energy_buy` - Grid import

### 3. Nastavit Dashboard

Zkopírovat karty z `examples/lovelace.yaml` do Lovelace dashboardu:
- Status card pro přehled
- ApexCharts pro vizualizaci plánu
- Ceny s prahovými hodnotami

### 4. Volitelně: Přidat Automatizace

Z `examples/automations.yaml` vybrat a přizpůsobit:
- Notifikace při změně režimu
- Bezpečnostní stop při vysoké ceně
- Ranní přehled plánu

## 🐛 TROUBLESHOOTING

### Kontrola logů:
```yaml
logger:
  default: warning
  logs:
    custom_components.gw_smart_charging: debug
```

### Co hledat v logu:
- `"Turning ON charging"` - Integrace volá nabijeni_on
- `"Turning OFF charging"` - Integrace volá nabijeni_off
- `"Script execution successful"` - Script úspěšně zavolán
- `"Charging state unchanged"` - Žádná změna, script se nevolá

### Časté problémy:

1. **Skripty se nevolají**
   - Zkontrolovat: `automation_enabled: true` v diagnostice
   - Zkontrolovat: Správné názvy scriptů v konfiguraci
   - Zkontrolovat: Skripty existují a fungují

2. **ApexCharts prázdné**
   - Zkontrolovat: Atributy `data_15min` a `timestamps` existují
   - Zkontrolovat: ApexCharts card nainstalován
   - Použít příklady z `examples/lovelace.yaml`

3. **Špatné rozhodování**
   - Zkontrolovat: Cenové prahy (always/never charge price)
   - Zkontrolovat: SOC limity (min/max/target)
   - Zkontrolovat: Forecast data jsou správná

### Diagnostický senzor:
Nejlepší způsob kontroly - vše vidíte v `sensor.gw_smart_charging_diagnostics`:
- `last_script_state` - Potvrzuje volání scriptů
- `mode_distribution` - Ukazuje plánované režimy
- `should_charge_now` - Aktuální rozhodnutí

## 📈 DALŠÍ MOŽNÁ VYLEPŠENÍ

1. **Custom panel** - Dedikovaný panel místo entity list
2. **Grafické vizualizace** - Interaktivní timeline view
3. **Notifikace** - Push notifikace na mobil při změnách
4. **Historie** - Long-term statistiky nabíjení
5. **API integrace** - Direct GoodWe API místo scriptů
6. **Weather integration** - Vylepšený forecast s počasím

## ✅ VALIDACE

Všechny soubory validovány:
- ✅ Python syntax (všech 7 souborů)
- ✅ JSON formát (manifest.json, hacs.json)
- ✅ YAML formát (všechny example soubory)
- ✅ Git tag 1.4.0 vytvořen

## 📞 KONTAKT

Issues: https://github.com/someone11221/gw_smart_energy_charging/issues

---

**Verze:** 1.4.0  
**Datum:** November 2024  
**Status:** ✅ PRODUCTION READY
