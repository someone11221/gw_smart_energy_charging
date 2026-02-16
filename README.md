# Smart Battery Charging Controller v3.0.1

🚀 **Nejpokročilejší řešení pro inteligentní nabíjení domácích bateriových systémů a wallboxů v Home Assistant**

Kompletně přepsaná verze s modulární architekturou, chytrou predikcí cenových peaků a krásným moderním UI.

## 🎯 Co je nového v 3.0.1

### 🧠 Inteligentní predikce peaků
- **Automatická detekce cenových špiček** - identifikuje kdy budou vysoké ceny
- **Preventivní nabíjení** - zajistí dostatečné nabití baterie před peaky
- **Minimalizace nákladů** - nabíjí během nejlevnějších období
- **Adaptivní plánování** - přizpůsobuje se volatilitě cen

### 🏗️ Modulární architektura
```
custom_components/gw_smart_charging/
├── price_providers/       # Různé zdroje cen (OTE, Nanogreen, Nordpool, ENTSO-E)
├── battery_controllers/   # Různé typy baterií (GoodWe, Tesla, Huawei)
├── charging_strategies/   # Optimalizační algoritmy
└── ui/                   # Moderní dashboard s grafy
```

### 🎨 Krásné UI/UX
- **Živé grafy** - Chart.js grafy cen, SOC predikce
- **Real-time monitoring** - Okamžitý přehled o stavu baterie
- **Barevné indikátory** - Jasné vizuální zpětné vazby
- **Responzivní design** - Funguje na desktop i mobilu

### ⚡ Chytrá logika nabíjení

#### Strategické cíle:
1. **Nabít do plna za nejnižší ceny** ✅
2. **Připravit baterii před peaky** ✅  
3. **Nikdy nekupovat za drahé ceny** ✅
4. **Optimalizovat celkové náklady** ✅

#### Jak to funguje:

**1. Predikce peaků (48h lookahead)**
```python
# Analyzuje cenovou křivku
# Identifikuje vrcholy (top 25% cen nebo >1.5x průměr)
# Slučuje blízké peaky do jednoho
```

**2. Preventivní nabíjení**
```python
# Před každým peakem:
# - 4 hodiny předem: urgentní nabíjení pokud SOC < 80%
# - 24 hodin předem: plánované nabíjení v nejlevnějších slotech
# Cíl: SOC ≥ 80% před peakem
```

**3. Opportunistické full-charging**
```python
# Když jsou ultra-levné ceny (bottom 20%):
# - Nabije baterii do 95%
# - Maximální úspora na dalších 24h
```

**4. Bezpečnostní minimum**
```python
# SOC nikdy neklesne pod 20%
# Emergency charging pokud hrozí
```

## 📊 Priority nabíjení

Systém používá **4 úrovně priority**:

1. **KRITICKÁ** (Priority 1) 🔴
   - Emergency nabíjení (SOC < 20%)
   - Urgentní příprava na blízký peak (<4h)

2. **VYSOKÁ** (Priority 2) 🟠
   - Příprava na nadcházející peak (4-24h)
   - Preventivní nabíjení

3. **NORMÁLNÍ** (Priority 3) 🟢
   - Opportunistické full-charging při nízkých cenách
   - Standardní optimalizace

4. **VOLITELNÁ** (Priority 4) ⚪
   - Extra nabíjení pokud je to výhodné

## 🚀 Instalace

### Metoda 1: HACS (doporučeno)
1. Přidejte custom repository v HACS:
   ```
   https://github.com/someone11221/gw_smart_energy_charging
   ```
2. Klikněte na "Integrations" → "+" → "Smart Battery Charging Controller"
3. Stáhněte a restartujte Home Assistant
4. Přidejte integraci přes UI: Nastavení → Zařízení a služby → Přidat integraci

### Metoda 2: Manuální
1. Zkopírujte složku `custom_components/gw_smart_charging` do `config/custom_components/`
2. Restartujte Home Assistant
3. Přidejte integraci přes UI

## ⚙️ Konfigurace

### Krok 1: Zdroj cen
- **OTE** (doporučeno pro ČR) - spotové ceny z OTE
- **Nanogreen** - integrace Nanogreen
- **Nordpool** - severské trhy
- **ENTSO-E** - evropské trhy

### Krok 2: Bateriový systém
- **Typ**: GoodWe / Tesla / Huawei / Generic
- **SOC sensor**: `sensor.battery_state_of_charge`
- **Power sensor**: `sensor.battery_power`
- **Kapacita**: 17 kWh (upravte dle vaší baterie)
- **Nabíjecí skripty**: `script.nabijeni_on` / `script.nabijeni_off`

### Krok 3: Strategie
- **Min SOC před peakem**: 80% (doporučeno)
- **Cílové SOC (plné)**: 95%
- **Bezpečnostní minimum**: 20%
- **Nabíjecí výkon**: 5 kW

## 📱 Dashboard

Přístup na: `http://homeassistant.local:8123/api/gw_smart_charging/dashboard`

### Funkce dashboardu:
- ⚡ **Real-time SOC** s barevnou lištou
- 💰 **Aktuální cena** elektřiny
- 📅 **Naplánované sloty** s prioritami
- ⚠️ **Predikované peaky** s časem a cenou
- 📊 **Grafy**: Ceny 24h, SOC predikce
- 🎛️ **Ovládání**: Zapnout/Vypnout automatiku

## 🔧 Senzory

### `sensor.gw_smart_charging_battery_status`
Aktuální stav baterie (SOC, výkon, kapacita)

### `sensor.gw_smart_charging_charging_plan`
Kompletní nabíjecí plán se sloty a peaky

### `sensor.gw_smart_charging_price_forecast`
Předpověď cen na 24-48 hodin

### `sensor.gw_smart_charging_next_charging`
Kdy začne příští nabíjení

### `sensor.gw_smart_charging_statistics`
Statistiky a metrika kvality

### `sensor.gw_smart_charging_diagnostics`
Diagnostika systému

## 🔀 Switch

### `switch.gw_smart_charging_auto_charging`
Zapnutí/vypnutí automatického nabíjení

## 🛠️ Služby

### `gw_smart_charging.force_plan_update`
Vynutí přepočet nabíjecího plánu

### `gw_smart_charging.get_charging_schedule`
Vrátí kompletní plán pro automatizace

## 📈 Příklad plánu

```yaml
Naplánované sloty:
  - 01:00-02:00: →95% @ 1.85 CZK/kWh (P3: Opportunistic full charge)
  - 02:00-03:00: →95% @ 1.92 CZK/kWh (P3: Opportunistic full charge)
  - 14:00-15:00: →80% @ 2.15 CZK/kWh (P2: Prep for peak at 18:00)

Predikované peaky:
  - 18:00: 4.85 CZK/kWh
  - 19:00: 4.92 CZK/kWh
```

## 🎓 Pokročilé použití

### Vlastní price provider
```python
from .price_providers.base import PriceProvider

class MyCustomProvider(PriceProvider):
    async def async_update(self):
        # Implementace
        pass
```

### Vlastní battery controller
```python
from .battery_controllers.base import BatteryController

class MyBatteryController(BatteryController):
    async def start_charging(self):
        # Implementace
        pass
```

## 🐛 Troubleshooting

### Integrace se nenačte
```bash
# Zkontrolujte logy
journalctl -u home-assistant -f | grep gw_smart
```

### Nabíjení se nespouští
1. Zkontrolujte `switch.gw_smart_charging_auto_charging` = ON
2. Ověřte že existují naplánované sloty
3. Zkontrolujte funkčnost skriptů `script.nabijeni_on/off`

### Špatné ceny
1. Ověřte sensor `sensor.current_consumption_price_czk_kwh`
2. Zkontrolujte atributy `today_hourly_prices` a `tomorrow_hourly_prices`

## 📝 Changelog

### v3.0.1 (2024)
- ✨ Kompletní přepis architektury
- 🧠 Inteligentní predikce cenových peaků
- 📊 Krásné UI s Chart.js grafy
- 🔌 Modulární price providers
- 🔋 Modulární battery controllers
- ⚡ Chytrá nabíjecí strategie s 4 prioritami
- 📱 Responzivní dashboard
- 🎨 Moderní design

## 🤝 Podpora

- **Issues**: https://github.com/someone11221/gw_smart_energy_charging/issues
- **Diskuze**: https://github.com/someone11221/gw_smart_energy_charging/discussions

## 📄 Licence

MIT License - viz LICENSE soubor

## 👤 Autor

**Martin Rak**
- GitHub: [@someone11221](https://github.com/someone11221)
- Vytvořeno s pomocí GitHub Copilot a Claude AI

---

⭐ **Pokud se vám integrace líbí, dejte hvězdičku na GitHubu!**

🔋 **Happy charging!** ⚡
