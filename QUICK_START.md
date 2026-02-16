# Quick Start Guide - Smart Battery Charging v3.0.1

## 🚀 5minutová instalace

### 1. Instalace (2 minuty)

**HACS:**
```
HACS → Integrations → ⋮ → Custom repositories
→ https://github.com/someone11221/gw_smart_energy_charging
→ Download → Restart HA
```

### 2. Konfigurace (2 minuty)

**Přidat integraci:**
```
Nastavení → Zařízení a služby → + Přidat integraci
→ "Smart Battery Charging"
```

**Vyplnit:**
```
┌─────────────────────────────────────────┐
│ Price Provider: ote                     │
│ Price Sensor: sensor.current_consumption│
│              _price_czk_kwh              │
└─────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ Battery Type: goodwe                    │
│ SOC Sensor: sensor.battery_state_of_    │
│            charge                        │
│ Power Sensor: sensor.battery_power      │
│ Capacity: 17.0 kWh                      │
│ On Script: script.nabijeni_on           │
│ Off Script: script.nabijeni_off         │
└─────────────────────────────────────────┘
               ↓
┌─────────────────────────────────────────┐
│ Min SOC před peakem: 80%                │
│ Cílové SOC (full): 95%                  │
│ Bezpečnostní min: 20%                   │
│ Nabíjecí výkon: 5.0 kW                  │
│ Auto charging: ✓                        │
└─────────────────────────────────────────┘
```

### 3. Dashboard (1 minuta)

**Otevřít:**
```
http://homeassistant.local:8123/api/gw_smart_charging/dashboard
```

**Uvidíte:**
- 🔋 Aktuální SOC baterie
- 💰 Aktuální cena elektřiny
- 📅 Naplánované nabíjení
- ⚠️ Predikované peaky
- 📊 Grafy cen a SOC

## ✅ Ověření funkčnosti

### Zkontrolujte entity

Měli byste mít:
```
✓ sensor.gw_smart_charging_battery_status
✓ sensor.gw_smart_charging_charging_plan
✓ sensor.gw_smart_charging_price_forecast
✓ sensor.gw_smart_charging_next_charging
✓ sensor.gw_smart_charging_statistics
✓ sensor.gw_smart_charging_diagnostics
✓ switch.gw_smart_charging_auto_charging
```

### Zkontrolujte plán

**Developer Tools → Services:**
```yaml
service: gw_smart_charging.get_charging_schedule
```

**Response by měla obsahovat:**
```json
{
  "slots": [...],
  "predicted_peaks": [...],
  "total_cost": 45.2,
  "total_kwh": 8.5,
  "confidence": 0.85
}
```

## 🎯 Co teď?

### První den
1. ✅ Zkontrolujte že auto-charging je ON
2. 📊 Sledujte dashboard
3. 📝 Zkontrolujte logy (žádné chyby)
4. 🔋 Ověřte že se nabíjení spouští podle plánu

### První týden
1. 📈 Sledujte denní statistiky
2. 💰 Porovnejte náklady
3. ⚙️ Případně upravte parametry
4. 📱 Přidejte notifikace

## 📱 Lovelace karta

**Přidejte do dashboardu:**

```yaml
type: vertical-stack
cards:
  - type: entities
    title: Smart Battery Charging
    entities:
      - entity: sensor.gw_smart_charging_battery_status
        name: SOC
        icon: mdi:battery
      - entity: sensor.gw_smart_charging_price_forecast
        name: Aktuální cena
        icon: mdi:cash
      - entity: sensor.gw_smart_charging_next_charging
        name: Další nabíjení
        icon: mdi:clock-start
      - entity: switch.gw_smart_charging_auto_charging
        name: Automatika
  
  - type: custom:apexcharts-card
    header:
      title: Ceny elektřiny (24h)
    graph_span: 24h
    series:
      - entity: sensor.gw_smart_charging_price_forecast
        data_generator: |
          return entity.attributes.prices.map(p => {
            return [new Date(p.time).getTime(), p.price];
          });
```

## 🔔 Notifikace

**Oznámení o nabíjení:**

```yaml
automation:
  - alias: "Notifikace - Začíná nabíjení"
    trigger:
      - platform: state
        entity_id: switch.gw_smart_charging_auto_charging
        attribute: charging_active
        to: true
    action:
      - service: notify.mobile_app
        data:
          title: "⚡ Nabíjení baterie"
          message: >
            Začíná nabíjení za {{ states('sensor.gw_smart_charging_price_forecast') }} CZK/kWh.
            Další peak v {{ state_attr('sensor.gw_smart_charging_next_charging', 'hours_until') }}h.
```

**Varování před peakem:**

```yaml
automation:
  - alias: "Varování - Blíží se peak"
    trigger:
      - platform: time_pattern
        hours: "*"
    condition:
      - condition: template
        value_template: >
          {% set peaks = state_attr('sensor.gw_smart_charging_charging_plan', 'predicted_peaks') %}
          {% if peaks %}
            {% set next_peak = peaks[0] %}
            {% set peak_time = strptime(next_peak.time, '%Y-%m-%d %H:%M') %}
            {% set hours_until = (peak_time - now()).total_seconds() / 3600 %}
            {{ hours_until < 2 }}
          {% else %}
            false
          {% endif %}
    action:
      - service: notify.mobile_app
        data:
          title: "⚠️ Blíží se cenový peak"
          message: >
            Za méně než 2 hodiny začíná peak! 
            SOC: {{ states('sensor.gw_smart_charging_battery_status') }}%
```

## 🛠️ Pokročilé použití

### Přepnutí providera

**Nastavení → Zařízení a služby → Smart Battery Charging → KONFIGURACE**

```
Price Provider: nanogreen
↓
Sensor: sensor.is_currently_in_five_cheapest_hours
```

### Úprava parametrů

```
Min SOC před peakem: 85%  (konzervativnější)
nebo
Min SOC před peakem: 75%  (agresivnější úspory)
```

### Test mode

```yaml
# Dočasně vypnout automatiku
service: switch.turn_off
target:
  entity_id: switch.gw_smart_charging_auto_charging

# Sledovat co by dělal systém
entity: sensor.gw_smart_charging_charging_plan
atribut: slots
```

## 📊 Metriky úspěchu

**Po týdnu sledování:**

```yaml
# Průměrná cena za nabíjení
sensor:
  - platform: template
    sensors:
      avg_charging_price:
        value_template: >
          {{ state_attr('sensor.gw_smart_charging_statistics', 'avg_price') }}
        unit_of_measurement: 'CZK/kWh'

# Celkové úspory
sensor:
  - platform: template
    sensors:
      total_savings:
        value_template: >
          {{ state_attr('sensor.gw_smart_charging_statistics', 'total_savings') }}
        unit_of_measurement: 'CZK'
```

## 🎓 Pro experty

### Vlastní strategie

```python
# custom_components/gw_smart_charging/charging_strategies/my_strategy.py

from .intelligent import IntelligentChargingStrategy

class MyCustomStrategy(IntelligentChargingStrategy):
    def _identify_peaks(self, forecast):
        # Vlastní logika detekce peaků
        ...
```

### Integration s jinou automatizací

```yaml
automation:
  - alias: "Override nabíjení při přebytku solaru"
    trigger:
      - platform: numeric_state
        entity_id: sensor.pv_power
        above: 5000  # 5kW přebytek
    condition:
      - condition: state
        entity_id: switch.gw_smart_charging_auto_charging
        state: 'on'
    action:
      # Dočasně vypnout smart charging
      - service: switch.turn_off
        target:
          entity_id: switch.gw_smart_charging_auto_charging
      # Spustit nabíjení manuálně
      - service: script.nabijeni_on
      # Počkat 2 hodiny
      - delay: '02:00:00'
      # Zapnout zpět smart charging
      - service: switch.turn_on
        target:
          entity_id: switch.gw_smart_charging_auto_charging
```

## 💡 Tipy a triky

1. **Začněte konzervativně**
   - Min SOC před peakem: 90%
   - Sledujte týden
   - Postupně snižujte

2. **Sledujte grafy**
   - Dashboard aktualizovat denně
   - Zkontrolujte predikce vs realitu
   - Upravte parametry

3. **Kombinujte s FV**
   - Nechte prostor pro solární nabíjení
   - Smart charging se aktivuje až po západu

4. **Notifikace jsou klíčové**
   - Upozornění na peaky
   - Potvrzení nabíjení
   - Varování při problémech

5. **Backup plán**
   - Vytvořte manuální override
   - Nouzové nabíjení vždy k dispozici

## 🆘 Rychlá pomoc

**Problém:** Nabíjení nefunguje
```bash
# 1. Zkontroluj switch
Developer Tools → States → switch.gw_smart_charging_auto_charging

# 2. Zkontroluj plán
Developer Tools → States → sensor.gw_smart_charging_charging_plan

# 3. Zkontroluj logy
Nastavení → Systém → Protokoly → Filtr: "gw_smart"
```

**Problém:** Špatné ceny
```bash
# Zkontroluj sensor
Developer Tools → States → sensor.current_consumption_price_czk_kwh
→ Attributes → today_hourly_prices
```

**Problém:** Dashboard nefunguje
```bash
# Restart HA a zkus znovu
http://homeassistant.local:8123/api/gw_smart_charging/dashboard
```

---

**Gratuluji! Máš nastaveno inteligentní nabíjení!** 🎉⚡

**Podpora:** https://github.com/someone11221/gw_smart_energy_charging/issues
