# GW Smart Charging v1.7.0 - Release Notes

## 🎉 Autonomous Service & Statistics Release

Verze 1.7.0 přináší plně autonomní provoz integrace s denními statistikami, predikcemi a funkčními ApexCharts grafy.

## 🆕 Nové funkce

### 1. Daily Statistics Sensor
**`sensor.gw_smart_charging_daily_statistics`**

Nový senzor poskytující kompletní denní statistiky:
- **Plánované nabíjení ze sítě** (kWh) - stav senzoru
- **Plánované nabíjení ze solárů** (kWh)
- **Plánované vybíjení baterie** (kWh)
- **Odhadované náklady** (Kč)
- **Skutečné nabití dnes** (kWh)
- **Skutečné vybití dnes** (kWh)
- **Efektivita nabíjení** (%) - porovnání plán vs realita
- **Úspora oproti pausálu** (Kč) - výpočet úspory

**Použití:**
```yaml
- entity: sensor.gw_smart_charging_daily_statistics
  name: Plánované nabíjení ze sítě
- type: attribute
  entity: sensor.gw_smart_charging_daily_statistics
  attribute: savings_vs_flat_rate
  name: Úspora dnes
  suffix: " Kč"
```

### 2. Prediction Sensor
**`sensor.gw_smart_charging_prediction`**

Senzor pro sledování kvality ML predikce a forecastu:
- **Stav:** disabled/learning/low_confidence/medium_confidence/high_confidence
- **ML konfidence** - na základě počtu historických dnů
- **Forecast konfidence** - kvalita PV forecastu
- **Prediction quality score** (0-100) - celková kvalita predikce
- **Informace o dni** - víkend/pracovní den

**Atributy:**
- `ml_enabled`: Zda je ML predikce zapnutá
- `ml_history_days`: Počet dní historických dat
- `ml_confidence`: high/medium/low/none
- `forecast_confidence_score`: Score forecastu (0-1)
- `prediction_quality_score`: Celkový score (0-100)
- `is_weekend`: true/false
- `day_of_week`: Pondělí, Úterý, atd.

**Použití v automatizaci:**
```yaml
trigger:
  - platform: numeric_state
    entity_id: sensor.gw_smart_charging_prediction
    attribute: prediction_quality_score
    above: 70
action:
  - service: notify.mobile_app
    data:
      message: "Kvalita predikce je vysoká - nabíjení bude optimální!"
```

### 3. Funkční ApexCharts Dashboard
**`examples/lovelace_v1.7.0.yaml`**

Kompletně přepracovaný dashboard s funkčními grafy:
- ✅ **Opravený data_generator** - správné formátování dat pro ApexCharts
- ✅ **Null handling** - kontrola undefined hodnot
- ✅ **Timestamp parsing** - správné zobrazení časové osy
- ✅ **Multi-axis grafy** - power (kW) + SOC (%) na jednom grafu
- ✅ **Ceny s prahovými hodnotami** - vizualizace always/never charge prahů
- ✅ **Denní statistiky** - kompletní přehled plánování a úspor
- ✅ **ML predikce** - vizualizace kvality predikce

**Nové karty v dashboardu:**
1. **Status & Predikce** - aktuální stav + kvalita predikce
2. **Denní statistiky a úspory** - kompletní finanční přehled
3. **Plán nabíjení a SOC** - graf s power + SOC axes
4. **Ceny elektřiny a nabíjení** - ceny s prahovými hodnotami
5. **ML Predikce & Konfidence** - detaily predikčního modelu
6. **Konfigurace & Diagnostika** - technické informace
7. **Activity Log** - poslední aktivity systému

## 🔧 Vylepšení

### Autonomní provoz
- Integrace pracuje plně autonomně bez zásahu uživatele
- Automatické volání nabíjecích skriptů každé 2 minuty
- Chytré rozhodování založené na ML predikci a forecastu
- Activity log pro sledování všech změn

### Optimalizace zobrazení senzorů
- Všechny senzory mají správně nastavené ikony
- State class a device class pro korektní zobrazení v HA
- Formátované jednotky (kWh, %, Kč, W)
- Podrobné atributy pro každý senzor

### Savings calculation
- Výpočet úspory oproti průměrné ceně (pausál)
- Porovnání optimalizovaného nabíjení vs flat-rate
- Zobrazení v Kč pro snadné pochopení
- Denní i měsíční projekce úspor

## 📊 Senzory v1.7.0

### Hlavní senzory
1. `sensor.gw_smart_charging_status` - Status integrace
2. `sensor.gw_smart_charging_forecast` - PV forecast
3. `sensor.gw_smart_charging_price` - Ceny elektřiny
4. `sensor.gw_smart_charging_schedule` - Aktuální režim
5. `sensor.gw_smart_charging_soc_forecast` - SOC prognóza
6. `sensor.gw_smart_charging_diagnostics` - Diagnostika

### Nové v1.7.0
7. **`sensor.gw_smart_charging_daily_statistics`** - Denní statistiky
8. **`sensor.gw_smart_charging_prediction`** - ML predikce a konfidence

### Real-time metriky
9. `sensor.gw_smart_charging_battery_power` - Výkon baterie (W)
10. `sensor.gw_smart_charging_today_battery_charge` - Dnešní nabití (kWh)
11. `sensor.gw_smart_charging_today_battery_discharge` - Dnešní vybití (kWh)

### Automatizační senzory
12. `sensor.gw_smart_charging_next_grid_charge` - Příští nabíjení
13. `sensor.gw_smart_charging_next_battery_discharge` - Příští vybíjení
14. `sensor.gw_smart_charging_activity_log` - Activity log

### Series senzory (pro grafy)
15-20. `sensor.gw_smart_charging_series_*` - pv, load, battery_charge, battery_discharge, grid_import, soc_forecast

## 🎨 Příklady použití

### Notifikace o úsporách
```yaml
- alias: "Ranní přehled úspor"
  trigger:
    - platform: time
      at: "07:00:00"
  action:
    - service: notify.mobile_app
      data:
        title: "💰 Dnešní úspora"
        message: >
          Optimalizované nabíjení: {{ state_attr('sensor.gw_smart_charging_daily_statistics', 'estimated_grid_cost_czk') }} Kč
          Úspora: {{ state_attr('sensor.gw_smart_charging_daily_statistics', 'savings_vs_flat_rate') }} Kč
          Efektivita: {{ state_attr('sensor.gw_smart_charging_daily_statistics', 'charge_efficiency_pct') }}%
```

### Kontrola kvality predikce
```yaml
- alias: "Upozornění na nízkou kvalitu predikce"
  trigger:
    - platform: numeric_state
      entity_id: sensor.gw_smart_charging_prediction
      attribute: prediction_quality_score
      below: 40
  action:
    - service: notify.persistent_notification
      data:
        title: "⚠️ Nízká kvalita predikce"
        message: >
          Quality score: {{ state_attr('sensor.gw_smart_charging_prediction', 'prediction_quality_score') }}%
          ML dní: {{ state_attr('sensor.gw_smart_charging_prediction', 'ml_history_days') }}
          Forecast: {{ state_attr('sensor.gw_smart_charging_prediction', 'forecast_confidence_reason') }}
```

### Dashboard gauge pro prediction quality
```yaml
- type: gauge
  entity: sensor.gw_smart_charging_prediction
  attribute: prediction_quality_score
  name: Kvalita predikce
  min: 0
  max: 100
  severity:
    green: 70
    yellow: 40
    red: 0
```

## 📦 Instalace

1. Aktualizujte z v1.6.0 na v1.7.0 přes HACS
2. Restartujte Home Assistant
3. Nové senzory se automaticky objeví
4. Importujte nový dashboard z `examples/lovelace_v1.7.0.yaml`
5. Nainstalujte ApexCharts card pokud ještě nemáte: https://github.com/RomRider/apexcharts-card

## 🔄 Migrace z v1.6.0

Migrace je **bezproblémová**:
- ✅ Všechny existující senzory zůstávají
- ✅ Automatizace pokračují v běhu
- ✅ Žádné změny konfigurace
- ✅ Pouze přibydou 2 nové senzory
- ✅ Nový lovelace dashboard v samostatném souboru

## 🐛 Opravy chyb

- ✅ Opraven data_generator v ApexCharts (null handling)
- ✅ Opraveno zobrazení timestamps v grafech
- ✅ Opraveno formátování jednotek v dashboardu
- ✅ Vylepšeno zpracování chybějících atributů

## 📈 Výkon

- Žádný dopad na výkon (pouze 2 nové lehké senzory)
- Update interval zůstává 2 minuty
- ML predikce běží efektivně v paměti
- Statistiky se počítají real-time z již dostupných dat

## 🎯 Co dál?

V budoucích verzích plánujeme:
- 📊 Měsíční statistiky a trendy
- 🌤️ Integrace s počasím pro lepší predikce
- 📱 Push notifikace při optimálních cenách
- 💾 Export dat pro další analýzu
- 🔌 Podpora dalších typů baterií

## 📝 Poznámky

- Pro správné fungování ApexCharts je nutná instalace custom card
- ML predikce vyžaduje alespoň 7 dní pro medium confidence
- Savings calculation používá průměrnou cenu z aktuálního dne
- Všechny nové senzory respektují HA best practices

## 🙏 Děkujeme

Děkujeme za vaši zpětnou vazbu a návrhy na vylepšení!

---

**Version:** 1.7.0  
**Release Date:** 2025-11-10  
**Maintainer:** @someone11221
