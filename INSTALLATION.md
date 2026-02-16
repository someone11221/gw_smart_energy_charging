# Instalační návod - Smart Battery Charging v3.0.1

## 📋 Požadavky

### Home Assistant
- Home Assistant 2024.1.0 nebo novější
- Python 3.10+
- HACS (volitelné, ale doporučené)

### Senzory
Následující senzory musí existovat ve vašem Home Assistant:

#### Povinné:
- **SOC sensor** (`sensor.battery_state_of_charge`) - Stav nabití baterie v %
- **Battery power** (`sensor.battery_power`) - Aktuální výkon baterie ve W
- **Price sensor** (`sensor.current_consumption_price_czk_kwh`) - Ceny elektřiny

#### Doporučené:
- **Today charged** (`sensor.today_battery_charge`) - Kolik kWh bylo dnes nabito
- **Today discharged** (`sensor.today_battery_discharge`) - Kolik kWh bylo dnes vybito

### Skripty
Vytvořte tyto skripty pro ovládání nabíjení:

```yaml
# configuration.yaml nebo scripts.yaml

script:
  nabijeni_on:
    alias: "Zapnout nabíjení baterie"
    sequence:
      - service: select.select_option
        target:
          entity_id: select.goodwe_work_mode  # Upravte dle vaší integrace
        data:
          option: "Battery Charge"
    mode: single

  nabijeni_off:
    alias: "Vypnout nabíjení baterie"
    sequence:
      - service: select.select_option
        target:
          entity_id: select.goodwe_work_mode
        data:
          option: "Eco Mode"  # Nebo jiný výchozí režim
    mode: single
```

## 🚀 Instalace

### Metoda 1: HACS (doporučeno)

1. Otevřete HACS v Home Assistant
2. Klikněte na **Integrations**
3. Klikněte na menu (3 tečky) → **Custom repositories**
4. Přidejte:
   ```
   Repository: https://github.com/someone11221/gw_smart_energy_charging
   Category: Integration
   ```
5. Klikněte **Add**
6. Najděte "Smart Battery Charging Controller" v seznamu
7. Klikněte **Download**
8. Restartujte Home Assistant

### Metoda 2: Manuální instalace

1. Stáhněte nejnovější release z GitHubu
2. Rozbalte archiv
3. Zkopírujte složku `custom_components/gw_smart_charging` do:
   ```
   <config_dir>/custom_components/gw_smart_charging/
   ```
4. Restartujte Home Assistant

## ⚙️ Konfigurace

### Krok 1: Přidání integrace

1. Přejděte na **Nastavení** → **Zařízení a služby**
2. Klikněte **+ Přidat integraci**
3. Vyhledejte "Smart Battery Charging"
4. Klikněte na integraci

### Krok 2: Zdroj cen

Vyberte poskytovatele spotových cen:

#### OTE (Český trh)
```yaml
Price Provider: ote
Price Sensor: sensor.current_consumption_price_czk_kwh
```

Sensor musí mít atributy:
- `today_hourly_prices`: {0: 2.5, 1: 2.3, ..., 23: 3.1}
- `tomorrow_hourly_prices`: {0: 2.4, 1: 2.2, ..., 23: 3.0}

#### Nanogreen
```yaml
Price Provider: nanogreen
Nanogreen Sensor: sensor.is_currently_in_five_cheapest_hours
```

### Krok 3: Bateriový systém

#### GoodWe
```yaml
Battery Type: goodwe
SOC Sensor: sensor.battery_state_of_charge
Battery Power Sensor: sensor.battery_power
Battery Capacity: 17.0  # kWh
Charging Script On: script.nabijeni_on
Charging Script Off: script.nabijeni_off
```

**Důležité poznámky:**
- `battery_power`: Kladné hodnoty = vybíjení, záporné = nabíjení
- Kapacita v kWh (ne Ah!)

#### Tesla Powerwall
```yaml
Battery Type: tesla
SOC Sensor: sensor.powerwall_battery_now
Battery Power Sensor: sensor.powerwall_battery_power
Battery Capacity: 13.5
...
```

### Krok 4: Strategie nabíjení

```yaml
Min SOC Before Peak: 80        # % - Min nabití před peakem
Target SOC Full: 95            # % - Cíl při plném nabití
Min SOC Safety: 20             # % - Bezpečnostní minimum
Charging Power: 5.0            # kW - Nabíjecí výkon
Auto Charging: true            # Automatické řízení
```

**Vysvětlení parametrů:**

- **Min SOC Before Peak** (80%):
  - Systém zajistí toto SOC alespoň 2 hodiny před každým peakem
  - Pomáhá vyhnout se nákupu za drahé ceny
  
- **Target SOC Full** (95%):
  - Cílové SOC při opportunistickém nabíjení
  - Dosahuje se pouze při ultra-levných cenách (bottom 20%)
  
- **Min SOC Safety** (20%):
  - Absolutní minimum - systém nikdy nenechá SOC klesnout níže
  - Emergency nabíjení se spustí okamžitě
  
- **Charging Power** (5.0 kW):
  - Maximální nabíjecí výkon vašeho systému
  - Použije se pro výpočet délky nabíjení

## 🎨 Přístup k dashboardu

Po úspěšné instalaci otevřete:

```
http://homeassistant.local:8123/api/gw_smart_charging/dashboard
```

Nebo v prohlížeči na IP vašeho Home Assistanta:

```
http://192.168.1.100:8123/api/gw_smart_charging/dashboard
```

## ✅ Ověření instalace

### 1. Zkontrolujte entity

Měli byste vidět tyto entity:

**Senzory:**
- `sensor.gw_smart_charging_battery_status`
- `sensor.gw_smart_charging_charging_plan`
- `sensor.gw_smart_charging_price_forecast`
- `sensor.gw_smart_charging_next_charging`
- `sensor.gw_smart_charging_statistics`
- `sensor.gw_smart_charging_diagnostics`

**Switch:**
- `switch.gw_smart_charging_auto_charging`

### 2. Zkontrolujte logy

```bash
# Vyhledejte chyby v logu
journalctl -u home-assistant -f | grep gw_smart

# Nebo v HA UI:
# Nastavení → Systém → Protokoly
```

Měli byste vidět:
```
INFO: Setting up Smart Battery Charging Controller v3.0.1
INFO: Initialized SmartChargingCoordinator v3.0.1: provider=ote, controller=goodwe
INFO: Dashboard views registered
INFO: Smart Battery Charging setup complete
```

### 3. Otestujte nabíjení

1. Zapněte auto-charging:
   ```yaml
   service: switch.turn_on
   target:
     entity_id: switch.gw_smart_charging_auto_charging
   ```

2. Zkontrolujte plán:
   ```yaml
   service: gw_smart_charging.get_charging_schedule
   ```

3. Sledujte logy pro potvrzení spouštění nabíjení

## 🔧 Troubleshooting

### Integrace se nenačítá

**Problém:** Integrace není v seznamu
**Řešení:**
1. Zkontrolujte že složka je na správném místě
2. Restartujte HA
3. Vyčistěte cache prohlížeče (Ctrl+F5)

### Chyba při konfiguraci

**Problém:** "Cannot connect" nebo "Invalid auth"
**Řešení:**
1. Zkontrolujte existenci všech senzorů
2. Ověřte formát názvů senzorů (bez mezer, lowercase)
3. Zkontrolujte logy pro detailnější chybu

### Nabíjení se nespouští

**Problém:** Auto-charging je ON, ale nic se neděje
**Řešení:**
1. Zkontrolujte že existují naplánované sloty:
   ```
   Stav: sensor.gw_smart_charging_charging_plan
   Atribut: slots
   ```
2. Ověřte funkčnost skriptů manuálně
3. Zkontrolujte že aktuální čas spadá do některého slotu

### Dashboard se nezobrazuje

**Problém:** 404 Not Found na /api/gw_smart_charging/dashboard
**Řešení:**
1. Restartujte HA
2. Zkontrolujte že views.py jsou správně naimportovány
3. Ověřte v logu: "Dashboard views registered"

### Špatné ceny

**Problém:** Ceny jsou 0 nebo nesmyslné
**Řešení:**
1. Zkontrolujte price sensor:
   ```
   Developer Tools → States → sensor.current_consumption_price_czk_kwh
   ```
2. Ověřte atributy `today_hourly_prices` a `tomorrow_hourly_prices`
3. Formát musí být: `{0: 2.5, 1: 2.3, ...}`

## 📚 Další kroky

1. **Přizpůsobte parametry** dle vaší spotřeby
2. **Sledujte dashboard** prvních několik dní
3. **Vytvořte automatizace** s využitím služby `get_charging_schedule`
4. **Přidejte notifikace** pro kritické události
5. **Experimentujte** s různými strategiemi

## 💡 Tipy

- Začněte s konservativními hodnotami (min_soc_before_peak = 90%)
- Sledujte první týden a upravte podle potřeby
- Používejte dashboard pro monitoring
- Pravidelně kontrolujte logy
- Vytvořte zálohu konfigurace

## 🆘 Podpora

Pokud potřebujete pomoc:

1. Zkontrolujte dokumentaci na GitHubu
2. Prohledejte Issues
3. Vytvořte nový Issue s:
   - Verzí HA
   - Verzí integrace
   - Logy z problému
   - Screenshot konfigurace

---

**Happy charging!** ⚡🔋
