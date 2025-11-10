# GW Smart Charging

Pokročilá integrace pro optimalizaci nabíjení baterie GoodWe s využitím solárního forecastu a cen elektřiny. Pracuje v 15minutových intervalech pro maximální přesnost.

## Funkce

- **15minutová optimalizace** - Přesné řízení nabíjení v 15min intervalech (96 slotů/den)
- **Inteligentní plánování**:
  1. Priorita self-consumption (solární přebytek)
  2. Vybíjení baterie pro pokrytí spotřeby domu
  3. Nabíjení z gridu při nízkých cenách
- **Cenové prahové hodnoty**:
  - Always charge price: Vždy nabíjet, pokud cena pod touto hodnotou
  - Never charge price: Nikdy nenabíjet, pokud cena nad touto hodnotou
  - **Hystereze**: ±5% buffer kolem prahů pro prevenci oscilace
- **SOC limity**: Min/Max/Target pro ochranu a optimální využití baterie
- **Predikce spotřeby**: 
  - Využití historických dat pro přesnější plánování
  - **ML predikce**: Průměrování posledních 30 denních vzorů
- **Critical Hours**: Udržování vyššího SOC během peak hours (např. 17-21)
- **Automatické ovládání**: Switch pro zapínání/vypínání nabíjení podle plánu
- **Real-time monitoring**: Battery power a grid import senzory

## Senzory

Integration vytváří následující senzory:

- **GW Smart Charging Forecast Status** - Stav integrace
- **GW Smart Charging Forecast** - Solární forecast (15min data)
- **GW Smart Charging Price** - Ceny elektřiny (15min data)
- **GW Smart Charging Schedule** - Aktuální režim a plán nabíjení
- **GW Smart Charging SOC Forecast** - Predikce stavu baterie
- **GW Smart Charging Diagnostics** - 🆕 Kompletní diagnostika a stav integrace
- **GW Smart Charging Auto Charging** (switch) - Ovládání automatického nabíjení
- **Series senzory** (pro grafy):
  - Series pv - Solární výroba
  - Series load - Spotřeba domu
  - Series battery_charge - Nabíjení baterie
  - Series battery_discharge - Vybíjení baterie
  - Series grid_import - Odběr ze sítě
  - Series soc_forecast - Predikce SOC

## Instalace přes HACS

1. HACS → Settings → Custom repositories → Add repository  
   - Repository URL: https://github.com/someone11221/gw_smart_energy_charging  
   - Category: Integration
2. Po instalaci restartujte Home Assistant
3. Settings → Devices & Services → Add Integration → GW Smart Charging

## Konfigurace (UI)

### Senzory
- **forecast_sensor**: sensor.energy_production_d2 (15min PV forecast)
- **price_sensor**: sensor.current_consumption_price_czk_kwh (today/tomorrow hourly prices)
- **load_sensor**: sensor.house_consumption (current power in W)
- **daily_load_sensor**: sensor.house_consumption_daily (daily consumption pattern)
- **battery_power_sensor**: sensor.battery_power (real-time battery charge/discharge power)
- **grid_import_sensor**: sensor.energy_buy (grid import monitoring)
- **soc_sensor**: sensor.battery_state_of_charge (battery SOC %)
- **charging_on_script**: script.nabijeni_on (script to turn on charging)
- **charging_off_script**: script.nabijeni_off (script to turn off charging)

### Parametry baterie
- **battery_capacity_kwh**: Kapacita baterie (kWh) - výchozí 17
- **max_charge_power_kw**: Maximální nabíjecí výkon (kW) - výchozí 3.7
- **charge_efficiency**: Nabíjecí účinnost (0-1) - výchozí 0.95

### SOC limity
- **min_soc_pct**: Minimální SOC (%) - výchozí 10
- **max_soc_pct**: Maximální SOC (%) - výchozí 95
- **target_soc_pct**: Cílový SOC (%) - výchozí 90

### Cenové prahy
- **always_charge_price**: Vždy nabíjet pod (CZK/kWh) - výchozí 1.5
- **never_charge_price**: Nikdy nenabíjet nad (CZK/kWh) - výchozí 4.0
- **price_hysteresis_pct**: Hystereze kolem prahů (%) - výchozí 5.0

### Critical Hours (Peak Protection)
- **critical_hours_start**: Začátek kritických hodin (0-23) - výchozí 17
- **critical_hours_end**: Konec kritických hodin (0-23) - výchozí 21
- **critical_hours_soc_pct**: Target SOC během peak hours (%) - výchozí 80

### Machine Learning
- **enable_ml_prediction**: Zapnout ML predikci spotřeby - výchozí false

### Automatizace
- **enable_automation**: Povolit automatické ovládání skriptů nabíjení - výchozí true
- **switch_on_means_charge**: Switch ON = nabíjení

**Jak funguje automatizace (v1.4.0):**
1. Integrace se aktualizuje každé 2 minuty
2. Vyhodnotí aktuální 15min slot a rozhodne, zda nabíjet
3. Pokud se stav změnil, zavolá příslušný script:
   - `script.nabijeni_on` - zapnutí nabíjení
   - `script.nabijeni_off` - vypnutí nabíjení
4. Skripty se volají pouze při změně stavu (ne opakovaně)
5. Veškeré akce jsou logovány pro diagnostiku

**Diagnostický senzor:**
- Zobrazuje aktuální stav automatizace
- Informace o poslední akci skriptu
- Distribuci režimů v plánu
- Čas příštího nabíjení
- Konfiguraci senzorů a skriptů

## Rekonfigurace

Pro změnu senzorů nebo parametrů:
1. Settings → Devices & Services → GW Smart Charging
2. Klikněte na "Configure" (ikona ozubeného kola)
3. Upravte požadované hodnoty a uložte

Integration se automaticky znovu načte s novými nastaveními.

## Lovelace vizualizace

### 1. Status Card - Aktuální stav

Zobrazení aktuálního stavu integrace s diagnostikou:

```yaml
type: entities
title: GW Smart Charging Status
entities:
  - entity: sensor.gw_smart_charging_diagnostics
    name: Status
  - type: attribute
    entity: sensor.gw_smart_charging_diagnostics
    attribute: current_mode
    name: Aktuální režim
  - type: attribute
    entity: sensor.gw_smart_charging_diagnostics
    attribute: should_charge_now
    name: Mělo by nabíjet
  - type: attribute
    entity: sensor.gw_smart_charging_diagnostics
    attribute: current_price
    name: Aktuální cena
    suffix: ' CZK/kWh'
  - type: attribute
    entity: sensor.gw_smart_charging_diagnostics
    attribute: current_soc
    name: Aktuální SOC
    suffix: ' %'
  - type: attribute
    entity: sensor.gw_smart_charging_diagnostics
    attribute: charging_slots_today
    name: Nabíjecích slotů dnes
  - type: attribute
    entity: sensor.gw_smart_charging_diagnostics
    attribute: next_charge_time
    name: Další nabíjení
  - type: attribute
    entity: sensor.gw_smart_charging_diagnostics
    attribute: last_script_state
    name: Poslední stav skriptu
  - entity: switch.gw_smart_charging_auto_charging
    name: Auto nabíjení
```

### 2. ApexCharts - Plán nabíjení

Kompletní vizualizace plánu na 24 hodin:

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: GW Smart Charging - 24h plán
  show_states: true
  colorize_states: true
graph_span: 24h
span:
  start: day
now:
  show: true
  label: Teď
yaxis:
  - id: power
    decimals: 1
    apex_config:
      title:
        text: Výkon (kW)
  - id: soc
    opposite: true
    decimals: 0
    min: 0
    max: 100
    apex_config:
      title:
        text: SOC (%)
series:
  - entity: sensor.gw_smart_charging_series_pv
    name: Solární výroba
    type: area
    color: orange
    opacity: 0.3
    yaxis_id: power
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  - entity: sensor.gw_smart_charging_series_load
    name: Spotřeba domu
    type: line
    color: blue
    stroke_width: 2
    yaxis_id: power
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  - entity: sensor.gw_smart_charging_series_battery_charge
    name: Nabíjení baterie
    type: column
    color: green
    yaxis_id: power
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  - entity: sensor.gw_smart_charging_series_battery_discharge
    name: Vybíjení baterie
    type: column
    color: red
    yaxis_id: power
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  - entity: sensor.gw_smart_charging_series_soc_forecast
    name: SOC prognóza
    type: line
    color: purple
    stroke_width: 3
    yaxis_id: soc
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
```

### 3. Ceny elektřiny

Graf hodinových cen s označením prahů:

```yaml
type: custom:apexcharts-card
header:
  show: true
  title: Ceny elektřiny
graph_span: 24h
span:
  start: day
series:
  - entity: sensor.gw_smart_charging_price
    name: Cena
    type: line
    stroke_width: 2
    data_generator: |
      return entity.attributes.price_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
apex_config:
  annotations:
    yaxis:
      - y: 1.5
        borderColor: '#00FF00'
        label:
          text: 'Always Charge'
          style:
            background: '#00FF00'
      - y: 4.0
        borderColor: '#FF0000'
        label:
          text: 'Never Charge'
          style:
            background: '#FF0000'
```

### 4. Kompletní dashboard

Všechny karty najednou v jednom pohledu:

```yaml
type: vertical-stack
cards:
  - type: entities
    title: GW Smart Charging v1.4.0
    entities:
      - entity: sensor.gw_smart_charging_diagnostics
      - entity: switch.gw_smart_charging_auto_charging
      - entity: sensor.gw_smart_charging_schedule
      - entity: sensor.gw_smart_charging_soc_forecast
  
  - type: custom:apexcharts-card
    header:
      show: true
      title: Plán nabíjení - 24h
    graph_span: 24h
    span:
      start: day
    now:
      show: true
    series:
      # ... (viz příklad 2 výše)
```
