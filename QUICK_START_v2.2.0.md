# GW Smart Charging v2.2.0 - Rychlý start / Quick Start Guide

## 🇨🇿 Český návod

### Nové funkce v2.2.0
- 🌍 Podpora češtiny a angličtiny
- 📊 Tři interaktivní grafy na dashboardu
- 🎯 9 strategií nabíjení (přidáno 4 nové)
- ⏱️ Celohodinové nabíjecí cykly

### Instalace/Upgrade

#### HACS (doporučeno)
1. Otevřete HACS v Home Assistant
2. Přejděte do Integrations
3. Vyhledejte "GW Smart Charging"
4. Klikněte na **Aktualizovat** (nebo Instalovat)
5. Restartujte Home Assistant

#### Manuální instalace
1. Stáhněte nejnovější release
2. Zkopírujte `custom_components/gw_smart_charging` do config adresáře
3. Restartujte Home Assistant

### První konfigurace

1. **Přidání integrace**
   - Nastavení → Zařízení a Služby → Přidat integraci
   - Vyhledejte "GW Smart Charging"
   - Vyplňte senzory (viz příklad níže)

2. **Výběr jazyka**
   - Při konfiguraci vyberte: **cs** (Čeština) nebo **en** (English)
   - Výchozí: cs (Čeština)

3. **Výběr strategie nabíjení**
   - Doporučeno začít s: **Dynamická optimalizace**
   - Lze později změnit v Nastavení → Konfigurace

### Příklad konfigurace

```
Název: GW Smart Charging
Jazyk: cs
Strategie: Dynamická optimalizace
Celohodinové nabíjení: Ano

Senzory:
- Solární forecast: sensor.energy_production_d2
- Cena elektřiny: sensor.current_consumption_price_czk_kwh
- Spotřeba domu: sensor.house_consumption
- Denní spotřeba: sensor.house_consumption_daily
- SOC baterie: sensor.battery_state_of_charge
- Výkon baterie: sensor.battery_power
- Import ze sítě: sensor.energy_buy

Skripty:
- Zapnutí nabíjení: script.nabijeni_on
- Vypnutí nabíjení: script.nabijeni_off

Parametry baterie:
- Kapacita: 17.0 kWh
- Max nabíjecí výkon: 3.7 kW
- Účinnost: 0.95
- Min SOC: 10%
- Max SOC: 95%
- Cílový SOC: 90%

Cenové prahy:
- Vždy nabíjet pod: 1.5 CZK/kWh
- Nikdy nenabíjet nad: 4.0 CZK/kWh
```

### Dashboard

**Přístup k dashboardu:**
- URL: `http://your-ha-instance:8123/api/gw_smart_charging/dashboard`
- Nebo klikněte na "GW Smart Charging" v postranním menu

**Co najdete na dashboardu:**
- 📊 **Graf cen** - Ceny elektřiny s plánovaným nabíjením
- 🔋 **Graf SOC** - Předpověď stavu baterie na 24h
- ☀️ **Graf solární výroby** - Očekávaná produkce FV
- 🎛️ **Ovládací panel** - Aktivace/deaktivace integrace
- 📈 **Statistiky** - Živé metriky a diagnostika

### Výběr strategie nabíjení

#### Pro maximální úspory
→ **Dynamická optimalizace** nebo **TOU optimalizace**

#### Pro jednoduchost
→ **4 nejlevnější hodiny** nebo **6 nejlevnějších hodin**

#### Pro využití solárů
→ **Priorita solární**

#### Pro špičku spotřeby
→ **Redukce špiček**

#### Pro pravidelný režim
→ **Adaptivní chytrá**

### Změna nastavení

1. Nastavení → Zařízení a Služby
2. Najděte "GW Smart Charging"
3. Klikněte na **KONFIGURACE**
4. Změňte jazyk, strategii nebo parametry
5. Uložte - integrace se automaticky reloadne

### Často dotazy

**Q: Jak změním jazyk?**
A: Nastavení → Konfigurace → vyberte "cs" nebo "en"

**Q: Jak funguje celohodinové nabíjení?**
A: Systém vybírá celé hodiny (4x 15min) místo jednotlivých slotů. Lepší pro baterii.

**Q: Která strategie je nejlepší?**
A: Záleží na vašich prioritách. Pro úspory: Dynamická. Pro jednoduchost: 4 nejlevnější.

**Q: Můžu vypnout celohodinové nabíjení?**
A: Ano, v Nastavení → Konfigurace → Full Hour Charging → Ne

**Q: Kde vidím grafy?**
A: Dashboard na `/api/gw_smart_charging/dashboard`

---

## 🇬🇧 English Guide

### New in v2.2.0
- 🌍 Czech and English language support
- 📊 Three interactive dashboard charts
- 🎯 9 charging strategies (4 new ones added)
- ⏱️ Full-hour charging cycles

### Installation/Upgrade

#### HACS (recommended)
1. Open HACS in Home Assistant
2. Go to Integrations
3. Search for "GW Smart Charging"
4. Click **Update** (or Install)
5. Restart Home Assistant

#### Manual Installation
1. Download latest release
2. Copy `custom_components/gw_smart_charging` to config directory
3. Restart Home Assistant

### Initial Setup

1. **Add Integration**
   - Settings → Devices & Services → Add Integration
   - Search for "GW Smart Charging"
   - Fill in sensors (see example below)

2. **Select Language**
   - During setup choose: **cs** (Czech) or **en** (English)
   - Default: cs (Czech)

3. **Select Charging Strategy**
   - Recommended to start: **Dynamic Optimization**
   - Can be changed later in Settings → Configure

### Configuration Example

```
Name: GW Smart Charging
Language: en
Strategy: Dynamic Optimization
Full Hour Charging: Yes

Sensors:
- Solar forecast: sensor.energy_production_d2
- Electricity price: sensor.current_consumption_price_czk_kwh
- House consumption: sensor.house_consumption
- Daily consumption: sensor.house_consumption_daily
- Battery SOC: sensor.battery_state_of_charge
- Battery power: sensor.battery_power
- Grid import: sensor.energy_buy

Scripts:
- Charging ON: script.nabijeni_on
- Charging OFF: script.nabijeni_off

Battery parameters:
- Capacity: 17.0 kWh
- Max charge power: 3.7 kW
- Efficiency: 0.95
- Min SOC: 10%
- Max SOC: 95%
- Target SOC: 90%

Price thresholds:
- Always charge below: 1.5 CZK/kWh
- Never charge above: 4.0 CZK/kWh
```

### Dashboard

**Access dashboard:**
- URL: `http://your-ha-instance:8123/api/gw_smart_charging/dashboard`
- Or click "GW Smart Charging" in sidebar menu

**What's on the dashboard:**
- 📊 **Price Chart** - Electricity prices with planned charging
- 🔋 **SOC Chart** - Battery state forecast for 24h
- ☀️ **Solar Chart** - Expected PV production
- 🎛️ **Control Panel** - Activate/deactivate integration
- 📈 **Statistics** - Live metrics and diagnostics

### Choosing a Strategy

#### For maximum savings
→ **Dynamic Optimization** or **TOU Optimized**

#### For simplicity
→ **4 Lowest Hours** or **6 Lowest Hours**

#### For solar utilization
→ **Solar Priority**

#### For peak demand
→ **Peak Shaving**

#### For regular routine
→ **Adaptive Smart**

### Changing Settings

1. Settings → Devices & Services
2. Find "GW Smart Charging"
3. Click **CONFIGURE**
4. Change language, strategy or parameters
5. Save - integration reloads automatically

### FAQ

**Q: How do I change language?**
A: Settings → Configure → select "cs" or "en"

**Q: How does full-hour charging work?**
A: System selects whole hours (4x 15min) instead of individual slots. Better for battery.

**Q: Which strategy is best?**
A: Depends on priorities. For savings: Dynamic. For simplicity: 4 Lowest Hours.

**Q: Can I disable full-hour charging?**
A: Yes, Settings → Configure → Full Hour Charging → No

**Q: Where are the charts?**
A: Dashboard at `/api/gw_smart_charging/dashboard`

---

## 📚 Další zdroje / Additional Resources

### Dokumentace / Documentation
- `README.md` - Úplná dokumentace / Complete documentation
- `RELEASE_NOTES_v2.2.0.md` - Release notes
- `IMPLEMENTATION_v2.2.0.md` - Technické detaily / Technical details
- `CHARGING_LOGIC.md` - Logika nabíjení / Charging logic

### Podpora / Support
- **GitHub Issues**: https://github.com/someone11221/gw_smart_energy_charging/issues
- **Diskuze**: https://github.com/someone11221/gw_smart_energy_charging/discussions

---

**Užijte si GW Smart Charging v2.2.0! / Enjoy GW Smart Charging v2.2.0! 🎉**
