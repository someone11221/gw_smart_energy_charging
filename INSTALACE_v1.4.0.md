# GW Smart Charging v1.4.0 - Průvodce Instalací a Použitím

## 🎯 CO SE ZMĚNILO V 1.4.0

### Hlavní vylepšení:

1. **✅ AUTOMATICKÉ VOLÁNÍ SKRIPTŮ**
   - Integrace nyní **SAMA** volá `script.nabijeni_on` a `script.nabijeni_off`
   - Kontrola a akce každé **2 minuty** (místo 5 minut)
   - Skripty se volají **pouze při změně stavu** (ne opakovaně)
   - Detailní logování všech akcí

2. **✅ NOVÝ DIAGNOSTICKÝ SENZOR**
   - `sensor.gw_smart_charging_diagnostics`
   - Kompletní přehled stavu, konfigurace a logiky
   - Sledování posledního volání skriptu
   - Distribuce režimů, čas příštího nabíjení

3. **✅ APEXCHARTS KOMPATIBILITA**
   - Všechny senzory mají správný formát atributů
   - Připravené příklady karet pro okamžité použití
   - 5 series pro kompletní vizualizaci

## 🚀 RYCHLÁ INSTALACE

### Krok 1: Aktualizace přes HACS

```bash
# V terminálu (pokud chcete ručně)
git pull
git checkout 1.4.0
```

Nebo přes HACS:
1. HACS → Integrations
2. GW Smart Charging → Update
3. Restart Home Assistant

### Krok 2: Vytvoření Nabíjecích Skriptů

**DŮLEŽITÉ:** Integrace potřebuje tyto dva skripty pro funkčnost!

Přejděte do **Settings → Automations & Scenes → Scripts** a vytvořte:

#### Script 1: `nabijeni_on`

```yaml
alias: GW - Zapnout nabíjení
description: Zapne nabíjení baterie z gridu
icon: mdi:battery-charging
sequence:
  # Vyberte JEDNU z následujících variant podle vaší konfigurace:
  
  # VARIANTA A: Pokud máte GoodWe switch přímo
  - service: switch.turn_on
    target:
      entity_id: switch.goodwe_battery_charge_from_grid
  
  # VARIANTA B: Pokud ovládáte přes ModBus (odkomentujte a upravte)
  # - service: modbus.write_register
  #   data:
  #     hub: goodwe
  #     address: 45352
  #     value: 1
  
  # Logování pro diagnostiku (doporučeno ponechat)
  - service: logbook.log
    data:
      name: GW Smart Charging
      message: >
        Nabíjení ZAPNUTO - cena: {{ state_attr('sensor.gw_smart_charging_schedule', 'current_price') }} CZK/kWh
```

#### Script 2: `nabijeni_off`

```yaml
alias: GW - Vypnout nabíjení
description: Vypne nabíjení baterie z gridu
icon: mdi:battery-off
sequence:
  # Vyberte JEDNU z následujících variant podle vaší konfigurace:
  
  # VARIANTA A: Pokud máte GoodWe switch přímo
  - service: switch.turn_off
    target:
      entity_id: switch.goodwe_battery_charge_from_grid
  
  # VARIANTA B: Pokud ovládáte přes ModBus (odkomentujte a upravte)
  # - service: modbus.write_register
  #   data:
  #     hub: goodwe
  #     address: 45352
  #     value: 0
  
  # Logování pro diagnostiku (doporučeno ponechat)
  - service: logbook.log
    data:
      name: GW Smart Charging
      message: >
        Nabíjení VYPNUTO - režim: {{ states('sensor.gw_smart_charging_schedule') }}
```

**📝 Poznámka:** Další varianty skriptů najdete v `examples/scripts.yaml`

### Krok 3: Konfigurace Integrace

1. **Settings → Devices & Services**
2. Najděte **GW Smart Charging**
3. Klikněte na **Configure** (ozubené kolečko)
4. Zkontrolujte/nastavte:

**Skripty:**
- `charging_on_script`: `script.nabijeni_on`
- `charging_off_script`: `script.nabijeni_off`

**Senzory:**
- `forecast_sensor`: `sensor.energy_production_d2`
- `price_sensor`: `sensor.current_consumption_price_czk_kwh`
- `load_sensor`: `sensor.house_consumption`
- `daily_load_sensor`: `sensor.house_consumption_daily`
- `soc_sensor`: `sensor.battery_state_of_charge`

**Automatizace:**
- `enable_automation`: **✅ ANO** (důležité pro automatické volání skriptů!)

5. **Uložit** a počkat cca 2 minuty na první aktualizaci

### Krok 4: Přidání Dashboard Karty

Zkopírujte kompletní konfiguraci z `examples/lovelace.yaml` nebo minimálně:

```yaml
type: entities
title: GW Smart Charging Status
entities:
  - entity: sensor.gw_smart_charging_diagnostics
    name: Status
  - entity: sensor.gw_smart_charging_schedule
    name: Režim
  - entity: switch.gw_smart_charging_auto_charging
    name: Automatické nabíjení
```

Pro grafy (vyžaduje ApexCharts card):
```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Plán nabíjení - 24h
graph_span: 24h
series:
  - entity: sensor.gw_smart_charging_series_pv
    name: Solar
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  # ... další series (viz examples/lovelace.yaml)
```

## 🔍 JAK ZKONTROLOVAT, ŽE TO FUNGUJE

### 1. Kontrola Diagnostického Senzoru

**Developer Tools → States** → `sensor.gw_smart_charging_diagnostics`

Zkontrolujte atributy:
- ✅ `automation_enabled: true`
- ✅ `charging_on_script: script.nabijeni_on`
- ✅ `charging_off_script: script.nabijeni_off`
- ✅ `update_interval_minutes: 2`
- 👁️ `last_script_state`: `true`/`false`/`null`

### 2. Kontrola Logů

**Settings → System → Logs** (nebo Developer Tools)

Hledejte tyto zprávy:
```
[custom_components.gw_smart_charging.coordinator] Turning ON charging (slot XX, mode: grid_charge_cheap, price: 1.45 CZK/kWh)
[custom_components.gw_smart_charging.coordinator] Script execution successful, new state: True
```

Nebo:
```
[custom_components.gw_smart_charging.coordinator] Charging state unchanged (False), skipping script call
```

### 3. Test Manuálního Volání

Developer Tools → Services:

```yaml
service: script.turn_on
target:
  entity_id: script.nabijeni_on
```

Po spuštění zkontrolujte, zda se skutečně zapnulo nabíjení na GoodWe inverteru.

## 📊 CO VŠECHNO INTEGRACE DĚLÁ

### Každé 2 minuty:

1. **Načte data:**
   - Solární forecast (15min intervaly)
   - Ceny elektřiny (15min intervaly)
   - Spotřebu domu
   - Aktuální SOC baterie

2. **Vypočítá optimální plán:**
   - 96 slotů (24h × 4 = 15min intervaly)
   - Pro každý slot určí režim:
     - `solar_charge` - nabíjení ze solaru
     - `grid_charge_cheap` - nabíjení ze sítě (cena ≤ 1.5 CZK)
     - `grid_charge_optimal` - nabíjení ze sítě (optimální)
     - `grid_charge_critical` - nabíjení pro critical hours
     - `battery_discharge` - vybíjení baterie
     - `idle` - nečinnost

3. **Vyhodnotí aktuální slot:**
   - Zjistí, v jakém 15min slotu se nacházíme
   - Rozhodne: `should_charge: true/false`

4. **Zavolá příslušný script:**
   - Pokud se stav změnil: volá `nabijeni_on` nebo `nabijeni_off`
   - Pokud stejný: nic nevolá (úspora zatížení)

5. **Loguje akci:**
   - Zapíše do Home Assistant logu
   - Aktualizuje diagnostický senzor

## 🎨 VIZUALIZACE (APEXCHARTS)

### Instalace ApexCharts Card:

HACS → Frontend → Hledat "ApexCharts Card" → Install

### Základní Graf:

Viz `examples/lovelace.yaml` pro kompletní konfigurace včetně:
- Status karta s diagnostikou
- 24h plán se všemi 5 series
- Graf cen s prahovými hodnotami
- Mobile-friendly verze

### Series Senzory:

Každý má atribut `data_15min` (pole 96 hodnot) a `timestamps`:
- `sensor.gw_smart_charging_series_pv` - Solární výroba
- `sensor.gw_smart_charging_series_load` - Spotřeba
- `sensor.gw_smart_charging_series_battery_charge` - Nabíjení
- `sensor.gw_smart_charging_series_battery_discharge` - Vybíjení
- `sensor.gw_smart_charging_series_soc_forecast` - Prognóza SOC

## 🔧 TROUBLESHOOTING

### Problém: Skripty se nevolají

**Řešení:**
1. Zkontrolovat `automation_enabled: true` v diagnostice
2. Ověřit názvy scriptů (musí být přesně `script.nabijeni_on/off`)
3. Zkontrolovat, že skripty existují a fungují manuálně
4. Zkontrolovat logy (viz výše)

### Problém: ApexCharts prázdné

**Řešení:**
1. Nainstalovat ApexCharts card z HACS
2. Použít `data_generator` z příkladů
3. Zkontrolovat atributy senzorů (Developer Tools → States)
4. Použít přesně příklady z `examples/lovelace.yaml`

### Problém: Špatné rozhodování

**Řešení:**
1. Zkontrolovat cenové prahy v konfiguraci:
   - `always_charge_price`: 1.5 CZK/kWh
   - `never_charge_price`: 4.0 CZK/kWh
2. Zkontrolovat SOC limity:
   - `min_soc_pct`: 10%
   - `max_soc_pct`: 95%
   - `target_soc_pct`: 90%
3. Ověřit forecast a price senzory mají správná data

### Debug Logování:

`configuration.yaml`:
```yaml
logger:
  default: warning
  logs:
    custom_components.gw_smart_charging: debug
```

Restart Home Assistant a sledujte logy.

## 📁 SOUBORY S PŘÍKLADY

- `examples/scripts.yaml` - 6 variant skriptů
- `examples/automations.yaml` - 7 automatizací (notifikace, bezpečnost)
- `examples/lovelace.yaml` - Kompletní dashboard konfigurace
- `IMPLEMENTATION_SUMMARY.md` - Technická dokumentace

## 🆘 PODPORA

Problémy hlaste na: https://github.com/someone11221/gw_smart_energy_charging/issues

---

**Verze:** 1.4.0  
**Datum:** Listopad 2024  
**Status:** ✅ PRODUCTION READY

Přeji úspěšné nabíjení! ⚡🔋
