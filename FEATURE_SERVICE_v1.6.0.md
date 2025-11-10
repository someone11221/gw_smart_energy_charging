# GW Smart Charging - New Service and Sensors (v1.6.0)

## Nová služba: `get_charging_schedule`

Integrace nyní poskytuje vlastní službu pro získání detailních informací o plánu nabíjení baterie. Služba je optimalizována pro použití v automatizacích, skriptech a scénách.

### Použití služby

```yaml
service: gw_smart_charging.get_charging_schedule
response_variable: schedule_data
```

### Vrácená data

Služba vrací JSON objekt s následujícími informacemi:

#### 1. Aktuální stav (`current_status`)
- `time`: Aktuální čas (HH:MM)
- `slot`: Index aktuálního 15minutového slotu (0-95)
- `mode`: Aktuální režim (grid_charge_cheap, solar_charge, battery_discharge, atd.)
- `should_charge`: Zda má probíhat nabíjení ze sítě (true/false)
- `price_czk_kwh`: Aktuální cena elektřiny (CZK/kWh)
- `soc_pct`: Stav nabití baterie (%)
- `is_critical_hour`: Zda je kritická hodina (true/false)

#### 2. Plánované periody nabíjení ze sítě (`grid_charging_periods`)
Seznam všech plánovaných období nabíjení ze sítě obsahující:
- `start_time`: Čas začátku (HH:MM)
- `end_time`: Čas konce (HH:MM)
- `duration_minutes`: Délka trvání v minutách
- `mode`: Režim nabíjení (grid_charge_cheap, grid_charge_optimal, grid_charge_critical)
- `avg_price`: Průměrná cena elektřiny v období (CZK/kWh)
- `avg_soc_end`: Průměrné SOC na konci období (%)

#### 3. Plánované periody vybíjení baterie (`battery_discharge_periods`)
Seznam všech plánovaných období vybíjení baterie obsahující:
- `start_time`: Čas začátku
- `end_time`: Čas konce
- `duration_minutes`: Délka trvání
- `avg_discharge_kw`: Průměrný výkon vybíjení (kW)

#### 4. Plánované periody nabíjení ze solárů (`solar_charging_periods`)
Seznam všech plánovaných období nabíjení ze solárních panelů.

#### 5. Sloty s importem ze sítě (`grid_import_slots`)
Seznam 15minutových slotů, kdy se očekává odběr ze sítě (když spotřeba > FV + baterie):
- `time`: Čas slotu
- `expected_import_kw`: Očekávaný import ze sítě (kW)
- `price_czk_kwh`: Cena elektřiny
- `mode`: Režim

#### 6. Denní statistiky (`daily_statistics`)
- `total_grid_charge_kwh`: Celkové plánované nabíjení ze sítě (kWh)
- `total_solar_charge_kwh`: Celkové plánované nabíjení ze solárů (kWh)
- `total_battery_discharge_kwh`: Celkové plánované vybíjení baterie (kWh)
- `estimated_grid_cost_czk`: Odhadované náklady na nabíjení ze sítě (Kč)
- `grid_charging_periods_count`: Počet období nabíjení ze sítě
- `solar_charging_periods_count`: Počet období nabíjení ze solárů
- `battery_discharge_periods_count`: Počet období vybíjení baterie

#### 7. Metriky baterie (`battery_metrics`)
- `current_power_w`: Aktuální výkon baterie (W, kladné = vybíjení, záporné = nabíjení)
- `current_power_kw`: Aktuální výkon baterie (kW)
- `status`: Stav baterie (charging, discharging, idle)
- `soc_pct`: Stav nabití (%)
- `soc_kwh`: Stav nabití (kWh)
- `today_charge_kwh`: Dnešní nabíjení celkem (kWh)
- `today_discharge_kwh`: Dnešní vybíjení celkem (kWh)

#### 8. Metriky sítě (`grid_metrics`)
- `current_import_w`: Aktuální import ze sítě (W)
- `current_import_kw`: Aktuální import ze sítě (kW)
- `house_load_w`: Aktuální spotřeba domu (W)
- `house_load_kw`: Aktuální spotřeba domu (kW)
- `pv_power_w`: Aktuální výkon FV (W)
- `pv_power_kw`: Aktuální výkon FV (kW)

#### 9. Informace o optimalizaci (`optimization_info`)
- `ml_prediction_enabled`: Zda je zapnutá ML predikce (true/false)
- `ml_history_days`: Počet dní historických dat pro ML
- `battery_capacity_kwh`: Kapacita baterie (kWh)
- `target_soc_pct`: Cílové SOC (%)
- `always_charge_price`: Vždy nabíjet pod touto cenou (CZK/kWh)
- `never_charge_price`: Nikdy nenabíjet nad touto cenou (CZK/kWh)

### Příklady použití

#### Notifikace o plánu nabíjení
```yaml
- alias: "Ranní přehled plánu nabíjení"
  trigger:
    - platform: time
      at: "06:00:00"
  action:
    - service: gw_smart_charging.get_charging_schedule
      response_variable: schedule_data
    - service: notify.mobile_app
      data:
        title: "📊 Plán nabíjení baterie"
        message: >
          Grid nabíjení: {{ schedule_data.daily_statistics.grid_charging_periods_count }} období
          Celkem: {{ schedule_data.daily_statistics.total_grid_charge_kwh }} kWh
          Náklady: {{ schedule_data.daily_statistics.estimated_grid_cost_czk }} Kč
```

#### Kontrola před peak hours
```yaml
- alias: "Kontrola SOC před peak hours"
  trigger:
    - platform: time
      at: "16:00:00"
  action:
    - service: gw_smart_charging.get_charging_schedule
      response_variable: schedule_data
    - condition: template
      value_template: "{{ schedule_data.battery_metrics.soc_pct < 70 }}"
    - service: notify.persistent_notification
      data:
        title: "⚠️ Nízké SOC před peak hours"
        message: "Baterie má pouze {{ schedule_data.battery_metrics.soc_pct }}%"
```

#### Scéna založená na stavu nabíjení
```yaml
- alias: "Automatická scéna podle nabíjení"
  trigger:
    - platform: time_pattern
      minutes: "/15"
  action:
    - service: gw_smart_charging.get_charging_schedule
      response_variable: schedule_data
    - choose:
        - conditions:
            - condition: template
              value_template: "{{ schedule_data.current_status.mode in ['grid_charge_cheap', 'grid_charge_optimal'] }}"
          sequence:
            - service: scene.turn_on
              target:
                entity_id: scene.low_consumption_mode
```

## Nové senzory

### 1. `sensor.gw_smart_charging_next_grid_charge`
Zobrazuje čas příštího plánovaného nabíjení ze sítě.

**Stav**: Čas začátku nabíjení (např. "14:00") nebo "none"

**Atributy**:
- `next_start_time`: Čas začátku
- `next_end_time`: Čas konce
- `next_duration_minutes`: Délka v minutách
- `next_avg_price`: Průměrná cena (CZK/kWh)
- `next_mode`: Režim nabíjení
- `is_tomorrow`: Zda je zítra (true/false)
- `all_periods_today`: Seznam všech period dnes
- `total_periods`: Celkový počet period

**Použití v automatizaci**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.gw_smart_charging_next_grid_charge
condition:
  - condition: template
    value_template: "{{ trigger.to_state.state != 'none' }}"
action:
  - service: notify.mobile_app
    data:
      message: >
        Nabíjení naplánováno na {{ states('sensor.gw_smart_charging_next_grid_charge') }}
        Cena: {{ state_attr('sensor.gw_smart_charging_next_grid_charge', 'next_avg_price') }} Kč/kWh
```

### 2. `sensor.gw_smart_charging_next_battery_discharge`
Zobrazuje čas příštího plánovaného vybíjení baterie.

**Stav**: Čas začátku vybíjení nebo "none"

**Atributy**:
- `next_start_time`: Čas začátku
- `next_end_time`: Čas konce
- `next_duration_minutes`: Délka v minutách
- `next_avg_discharge_kw`: Průměrný výkon (kW)
- `all_periods_today`: Seznam všech period dnes

### 3. `sensor.gw_smart_charging_activity_log`
Zaznamenává změny aktivity systému a poskytuje log událostí.

**Stav**: Aktuální aktivita (např. "charging (grid_charge_cheap)", "discharging", "solar_charging")

**Atributy**:
- `activity_log`: Kompletní log všech změn (max 100 záznamů)
- `recent_activity`: Posledních 10 změn
- `total_log_entries`: Celkový počet záznamů
- `mode_transitions_today`: Počet přechodů mezi režimy
- `battery_status`: Aktuální stav baterie
- `current_soc_pct`: Aktuální SOC (%)
- `automation_active`: Zda je aktivní automatizace
- `last_script_state`: Stav posledního volání skriptu

**Použití**:
```yaml
trigger:
  - platform: state
    entity_id: sensor.gw_smart_charging_activity_log
action:
  - service: logbook.log
    data:
      name: "Battery Activity"
      message: "{{ states('sensor.gw_smart_charging_activity_log') }}"
```

## Vylepšená optimalizace

### ML predikce spotřeby (v1.6.0)
Algoritmus byl vylepšen o:
- **Vážené průměrování**: Novější dny mají vyšší váhu v predikci
- **Exponenciální rozpad**: Dávnější data mají menší vliv
- **Bezpečnostní marže**: 10% navýšení predikce pro prevenci podhodnocení

### Chytřejší rozhodování o nabíjení ze sítě
Nová logika zohledňuje:
1. **Budoucí deficit energie**: Vypočítává očekávaný nedostatek energie z rozdílu spotřeby a FV výroby
2. **Kapacita baterie**: Respektuje limity baterie, nepřebíjí
3. **Kritické hodiny**: Agresivnější nabíjení před peak hours
4. **Minimální prah**: Nabíjí pouze pokud je potřeba > 0.5 kWh (prevence zbytečných cyklů)

**Výpočet**:
```
energie_potřebná = (cílové_SOC - aktuální_SOC) + očekávaný_deficit
kde:
  očekávaný_deficit = max(0, budoucí_spotřeba - budoucí_FV_výroba)
```

### Příklad optimalizace
```
Aktuální SOC: 40% (6.8 kWh z 17 kWh)
Cílové SOC: 90% (15.3 kWh)
Budoucí FV výroba: 8 kWh
Budoucí spotřeba: 12 kWh
Očekávaný deficit: 4 kWh
Energie potřebná: (15.3 - 6.8) + 4 = 12.5 kWh

-> Systém naplánuje nabíjení v levných hodinách pro pokrytí 12.5 kWh
```

## Shrnutí vylepšení v1.6.0

✅ **Nová služba** `get_charging_schedule` pro automatizace  
✅ **3 nové senzory** pro snadný přístup k datům  
✅ **Vylepšená ML predikce** s váženým průměrováním  
✅ **Chytřejší grid charging** založené na budoucích potřebách  
✅ **Activity log** pro sledování změn  
✅ **Příklady automatizací** v `examples/automations.yaml`
