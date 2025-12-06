# Smart Battery Charging Controller

Pokročilá integrace pro Home Assistant optimalizující nabíjení baterie pomocí solárního forecastu a cen elektřiny. **Verze 2.4.0** - Vylepšená optimalizace nákladů, nový senzor sledování úspor, lepší validace senzorů.

**Autor:** Martin Rak | **Firmware verze:** 2.4.0

## Funkce

### 🆕 Nové ve v2.4.0

💰 **Vylepšená optimalizace nákladů** - Agresivnější hledání nejlevnějších hodin pro maximální úspory  
📊 **Nový senzor sledování nákladů** - Kompletní přehled nákladů, úspor a efektivity nabíjení  
🔍 **Detekce volatility cen** - Automatické rozpoznání vysoké volatility a přizpůsobení strategie  
⏰ **Prodloužené okno předpovědi** - 18 hodin místo 12 pro lepší plánování  
🎯 **Citlivější detekce trendů** - 5% práh místo 10% pro zachycení menších rozdílů v cenách  
📈 **Lepší validace senzorů** - Robustnější zpracování chybějících nebo nedostupných senzorů  
🔧 **Diagnostika kvality dat** - Sledování kvality dat z každého senzoru  
💡 **Vylepšené logování** - Informativnější zprávy o rozhodnutích týkajících se cen  

### 🆕 Nové ve v2.3.0

📊 **Vylepšený dashboard** - Zobrazení aktuální strategie nabíjení, SOC, test mode status, příští nabíjení  
🎨 **Lepší konfigurace UI** - Emoji ikony, detailní popisky a hinty ke každému parametru  
🧪 **Rozšířený test mode** - Podrobné vysvětlení co testovat a jak používat simulační režim  
📈 **Data debugging** - Přidána sekce s informacemi o dostupnosti dat pro grafy  
🔍 **Console logging** - Vylepšené logování pro diagnostiku problémů s grafy  
📝 **CHANGELOG.md** - Nový soubor pro HACS zobrazení změn při aktualizaci  
👤 **Branding update** - Změna výrobce na Martin Rak, verze shodná s tagem  
💡 **Hints všude** - Vysvětlivky a rady v dashboardu i konfiguraci  

### 🆕 Nové ve v2.2.0

🌍 **Vícejazyčná podpora** - Přepínání mezi češtinou a angličtinou v celém rozhraní  
📊 **Interaktivní grafy** - Tři dynamické Chart.js grafy: ceny, SOC predikce, solární výroba  
🎯 **4 nové strategie** - Adaptivní chytrá, Priorita solární, Redukce špiček, TOU optimalizace  
⏱️ **Celohodinové cykly** - Nabíjení v celých hodinách (4x 15min sloty) pro lepší stabilitu  
🎨 **Vylepšený dashboard** - Živé grafy s překryvem plánovaného nabíjení  
⚙️ **Rozšířená konfigurace** - Výběr jazyka a typu nabíjení přímo v UI  

### 🆕 Nové ve v2.1.0

🎯 **Strategie nabíjení** - 5 různých strategií: dynamická optimalizace, 4/6 nejlevnějších hodin, Nanogreen, cenový práh  
⚡ **Vylepšená 12h predikce** - Chytřejší detekce cenových trendů s 10% prahem a čekání na absolutní minimum  
🔧 **Opravený dashboard** - Vyřešena chyba JSON parsování, fungující tlačítka aktivace/deaktivace  
📦 **Konzistentní verze** - Všechny komponenty zobrazují správnou verzi 2.1.0  
📝 **Lepší logování** - Detailní informace o výběru strategie a cenových rozhodnutích  

### Nové ve v2.0.0

🎛️ **Nanogreen integrace** - Automatické nabíjení během 5 nejlevnějších hodin z `sensor.is_currently_in_five_cheapest_hours`  
🧠 **Pokročilé ML vzory** - Samostatné predikce pro pracovní dny, víkendy a svátky  
🔌 **Řízení přídavných spínačů** - Automatické zapínání/vypínání spínačů podle ceny elektřiny  
🧪 **Testovací režim** - Bezpečné testování a ladění bez skutečného ovládání  
🌍 **Detekce svátků** - Rozpoznání českých svátků pro lepší predikce  

### Základní funkce

✨ **Automatické autonomní řízení** - Aktivní ovládání nabíjení každé 2 minuty bez zásahu uživatele  
🎯 **15minutová optimalizace** - Přesné řízení v 96 intervalech/den  
🌞 **Inteligentní self-consumption** - Priorita využití solárního přebytku  
💰 **Cenové prahové hodnoty** - Always/Never charge prahy s hysterezí  
🔋 **SOC limity** - Min/Max/Target pro ochranu baterie  
📊 **Denní statistiky** - Plánované vs skutečné nabíjení, úspory, efektivita  
🔮 **Vylepšená ML Predikce** - Vážené průměrování z 30 dní historických dat s quality score  
⚡ **Critical Hours** - Vyšší SOC během peak hours  
🤖 **Script automation** - Automatické volání script.nabijeni_on/off  
📈 **Real-time monitoring** - Battery power & grid import  
🔍 **Diagnostika** - Kompletní přehled stavu a logiky integrace s aktuálním SoC  
🔄 **W→kWh konverze** - Automatický převod jednotek pro správnou logiku  
📉 **Sledování nabíjení/vybíjení** - Today's charge/discharge tracking  
🛠️ **Služba pro automatizace** - `get_charging_schedule` s detailními údaji  
📝 **Activity log** - Sledování změn režimů a stavu systému  
💡 **Prediction sensor** - Konfidence ML a forecastu, kvalita predikce  
💸 **Savings tracking** - Úspory oproti pausálnímu tarifu  
📱 **Device Panel** - Kompletní integrace v Zařízení a Služby  
🎨 **Zjednodušené entity** - Pouze 9 základních senzorů + 1 switch  
🎴 **Custom Lovelace Card** - Profesionální karta s kompaktním přehledem a 24h predikcí  
⚙️ **Options Flow** - Rekonfigurace bez reinstalace  
🔲 **Panel v postranní liště** - Přímý přístup k dashboardu  
🧠 **Optimální nabíjení** - Čeká na nejlevnější hodinu při klesající ceně  
🎛️ **Ovládací panel** - Aktivace/deaktivace a konfigurace z dashboardu  
🔮 **24h predikce** - Vizualizace plánu nabíjení/vybíjení na další den  

## Instalace

1. Add repository to HACS (type: Integration):  
   `https://github.com/someone11221/gw_smart_energy_charging`
2. Install via HACS → Integrations
3. Restart Home Assistant
4. Add integration through Settings → Devices & Services → Add Integration → GW Smart Charging
5. Access dashboard at: `/api/gw_smart_charging/dashboard`

## Konfigurace

Integrace podporuje následující senzory:
- `sensor.energy_production_d2` - 15min PV forecast (watts attribute) → automaticky převedeno na kWh
- `sensor.current_consumption_price_czk_kwh` - Ceny elektřiny (today/tomorrow_hourly_prices)
- `sensor.house_consumption` - Aktuální spotřeba (W) → automaticky převedeno na kWh
- `sensor.house_consumption_daily` - Denní spotřeba (kWh)
- `sensor.battery_power` - Real-time nabíjecí/vybíjecí výkon (W, **kladné hodnoty = vybíjení, záporné = nabíjení**)
- `sensor.energy_buy` - Grid import monitoring (W) → automaticky převedeno na kWh
- `sensor.battery_state_of_charge` - SOC baterie (%), kapacita 17 kWh
- `sensor.today_battery_charge` - Kolik kWh bylo dnes do baterie uloženo
- `sensor.today_battery_discharge` - Kolik kWh bylo dnes z baterie odebráno
- `sensor.pv_power` - Aktuální výroba solárních panelů (W) → automaticky převedeno na kWh
- `sensor.is_currently_in_five_cheapest_hours` - **NOVÉ v2.0** Nanogreen senzor nejlevnějších hodin (volitelné)
- `script.nabijeni_on` - Script pro zapnutí nabíjení
- `script.nabijeni_off` - Script pro vypnutí nabíjení

### Nové v2.0: Přídavné spínače

Můžete přidat libovolné spínače z Home Assistantu, které se budou automaticky zapínat/vypínat podle ceny elektřiny:

**Příklad konfigurace:**
- Additional Switches: `switch.bojler,switch.cerpadlo,switch.nabijeni_ev`
- Switch Price Threshold: `2.0` CZK/kWh

**Jak to funguje:**
- Když cena elektřiny klesne pod 2.0 CZK/kWh → zapne bojler, čerpadlo, EV nabíjení
- Když cena elektřiny stoupne nad 2.0 CZK/kWh → vypne bojler, čerpadlo, EV nabíjení

**Vhodné použití:**
- Elektrické bojlery
- Bazénová čerpadla
- Nabíječky elektromobilů
- Pračky, myčky
- Jakékoliv energeticky náročné spotřebiče

**Důležité:** Všechny výkonové senzory (W) jsou automaticky převáděny na kWh pro správnou logiku integrace.

Parametry včetně cenových prahů, SOC limitů, hystereze a critical hours lze nastavit přes UI.

## Dashboard

Integrace poskytuje přehledný dashboard podobný open-meteo integraci:
- Zobrazení všech senzorů z integrace
- Výpis aktivity integrace
- Statistiky a diagnostika
- Real-time monitoring baterie a sítě

Dashboard je dostupný na: `/api/gw_smart_charging/dashboard`

**NOVINKA v1.9.0**: Panel je nyní integrován přímo v postranní liště Home Assistentu! Klikněte na ikonu "GW Smart Charging" v menu pro přístup k dashboardu.

## Custom Lovelace Card (v1.9.0)

Integrace poskytuje vlastní Lovelace kartu pro kompaktní přehled všech klíčových metrik:

### Použití karty
```yaml
type: custom:gw-smart-charging-card
entity: sensor.gw_smart_charging_diagnostics
```

### Funkce karty
- ⚡ **Real-time SOC** - Vizuální gradient lišta (červená→žlutá→zelená)
- 📊 **Klíčové metriky** - Peak forecast, aktuální cena, plánované nabíjení, další nabíjení
- 🎨 **Barevné indikátory** - Režimy nabíjení s barvami (grid_charge, solar_charge, battery_discharge, self_consume)
- 🔄 **Integrovaný switch** - Ovládání automatického nabíjení přímo z karty
- 📱 **Responzivní design** - Funguje na desktop i mobile

Karta je automaticky registrována po instalaci integrace.

## Rekonfigurace (v1.9.0)

**Options Flow** umožňuje změnit konfiguraci bez reinstalace:

1. Přejděte na Nastavení → Zařízení a Služby
2. Najděte "GW Smart Charging"
3. Klikněte na **KONFIGURACE**
4. Změňte senzory nebo parametry
5. Uložte - integrace se automaticky reloadne

Žádná ztráta dat, žádná reinstalace!

## Senzory (v2.4.0)

Integrace poskytuje **10 základních senzorů** a **1 switch**:

### Hlavní senzory
1. **`sensor.gw_smart_charging_forecast`** - Solární forecast s cenami elektřiny
2. **`sensor.gw_smart_charging_schedule`** - Aktuální plán nabíjení
3. **`sensor.gw_smart_charging_soc_forecast`** - Předpověď SOC s daty pro grafy
4. **`sensor.gw_smart_charging_battery_power`** - Výkon baterie a dnešní součty

### Diagnostika a statistiky
5. **`sensor.gw_smart_charging_diagnostics`** - Diagnostika systému s aktuálním SoC a kvalitou senzorů
6. **`sensor.gw_smart_charging_daily_statistics`** - Denní statistiky a úspory
7. **`sensor.gw_smart_charging_prediction`** - Kvalita ML predikce
8. **`sensor.gw_smart_charging_cost_optimization`** - **NOVÉ v2.4.0** - Sledování nákladů a úspor

### Automatizace
9. **`sensor.gw_smart_charging_next_charge`** - Další plánované nabíjení/vybíjení
10. **`sensor.gw_smart_charging_activity_log`** - Historie aktivit

### Ovládání
11. **`switch.gw_smart_charging_auto_charging`** - Automatické řízení

**Poznámka:** Data z předchozích 11 senzorů (series, today charge/discharge, atd.) jsou nyní dostupná jako atributy konsolidovaných senzorů. Viz `RELEASE_NOTES_v1.8.0.md` pro detaily migrace.

## Dokumentace logiky nabíjení

Detailní dokumentace logiky nabíjení je v `/CHARGING_LOGIC.md`. Tento dokument obsahuje:
- Popis všech použitých senzorů a jejich účelu
- Krok za krokem proces rozhodování
- Příklady scénářů pro různé denní doby
- Vysvětlení všech režimů nabíjení
- Konfigurace parametrů

## Nové v1.9.5

### Optimální Načasování Nabíjení
- **Detekce cenového trendu** - Rozpozná klesající tendenci cen elektřiny
- **Čekání na minimum** - Místo nabíjení při první levné hodině čeká na nejlevnější
- **Maximální úspory** - Vybírá optimální okamžik pro start nabíjení
- **Inteligentní okna** - Balancuje mezi úsporou a potřebou nabít včas

### Ovládací Panel v Dashboardu
- ✅ **Tlačítko Aktivace** - Zapnutí automatického nabíjení jedním kliknutím
- 🛑 **Tlačítko Deaktivace** - Vypnutí automatického nabíjení
- ⚙️ **Přímý odkaz na konfiguraci** - Rychlý přístup k nastavení
- 🧪 **Testovací režim** - Příprava na budoucí testování strategií

### 24-hodinová Predikce
- **Vizuální timeline** - Zobrazení plánovaných akcí na další den
- **Barevné indikátory** - Nabíjení ze sítě/solaru, vybíjení baterie
- **SOC prognóza** - Očekávaná úroveň baterie v čase
- **Automatická aktualizace** - Refresh každých 15 minut
- **Dostupné na 2 místech:**
  - Dashboard (`/api/gw_smart_charging/dashboard`)
  - Lovelace karta

### Vylepšená Lovelace Karta
- **Integrovaná timeline** - 24h predikce přímo v kartě
- **Kompaktní zobrazení** - Top 8 významných událostí
- **Vizuální ikony** - 🌞 Solar, ⚡ Grid, 🔋 Battery
- **Real-time aktualizace** - Živé sledování změn

### Příklad použití
```yaml
# Scénář: Ceny elektřiny klesají přes noc
# 22:00 = 3.5 CZK, 23:00 = 3.2 CZK, 00:00 = 2.8 CZK, 01:00 = 2.5 CZK

# Staré chování (v1.9.0):
# Začne nabíjet v 22:00 (první levná hodina)

# Nové chování (v1.9.5):  
# Detekuje klesající trend → čeká → začne v 01:00
# Úspora: 1.0 CZK/kWh! ⚡💰
```

## Nové v1.9.0

### Custom Lovelace Card
- **Profesionální karta** s kompaktním přehledem všech metrik
- **Vizuální SOC lišta** s gradientem (červená→žlutá→zelená)
- **Klíčové metriky** na jednom místě
- **Barevné indikátory** režimů nabíjení
- **Integrovaný switch** pro ovládání

### Panel v Postranní Liště
- **Přímý přístup** k dashboardu z menu
- **Ikona baterie** v postranní liště
- **Dostupné všem uživatelům** (ne jen admin)

### Options Flow
- **Rekonfigurace bez reinstalace** - změňte senzory/parametry přes UI
- **Automatické reload** po změně
- **Žádná ztráta dat** při úpravě konfigurace
- Cesta: Nastavení → Zařízení a Služby → GW Smart Charging → KONFIGURACE

### Energy Dashboard Integrace
- **Proper device_class** na všech energetických senzorech
- **State_class** pro správné měření
- **Připraveno pro HA Energy Dashboard**

## Nové v1.8.0

### Device Panel Integrace
Integrace se nyní zobrazuje v panelu Zařízení a Služby:
- Všechny entity přístupné z jednoho místa
- Přehledná organizace senzorů a ovládání
- Snadná diagnostika a konfigurace

### Konsolidace entit
- **Zredukováno z 21 na 10 entit** - Jednodušší přehled
- **Série data** - Přesunuta do atributů `sensor.gw_smart_charging_soc_forecast`
- **Today's totals** - Dostupné v atributech `sensor.gw_smart_charging_battery_power`
- **Ceny** - Sloučeny do `sensor.gw_smart_charging_forecast`
- **Next periods** - Sloučeny do `sensor.gw_smart_charging_next_charge`

### Opravy
- **Diagnostika** - Nyní správně zobrazuje aktuální SoC ze `sensor.battery_state_of_charge`
- **Lepší pochopitelnost** - Jasné názvy a popisy senzorů

### Dokumentace
- **CHARGING_LOGIC.md** - Kompletní dokumentace logiky nabíjení
- **RELEASE_NOTES_v1.8.0.md** - Detailní release notes s migrační příručkou

## Release Notes

### v2.4.0 (Cost Optimization & Sensor Reliability - December 2024)

#### 💰 Enhanced Cost Optimization

**New Cost Tracking Sensor**
- `sensor.gw_smart_charging_cost_optimization` provides comprehensive cost metrics
- Daily grid charging cost and savings tracking
- Monthly/yearly savings estimates
- Optimization score (0-100) showing efficiency
- Price volatility tracking and analysis

**Smarter Price Targeting**
- More aggressive optimization (5% threshold vs 10%)
- Extended 18-hour lookahead window (was 12h)
- Price volatility detection for dynamic pricing
- Better handling of spot price variations

**Cost Optimization Modes**
- Automatically detects high price volatility (>30%)
- Uses only cheapest 25% of slots when prices vary significantly
- Smarter waiting for absolute price minimums
- Better balance between cost and battery readiness

#### 🔧 Improved Sensor Reliability

**Enhanced Validation**
- Checks for unavailable/unknown sensor states
- Better error handling and recovery
- Detailed sensor quality tracking
- Informative logging of sensor issues

**Diagnostics Enhancements**
- New sensor quality attributes
- `sensor_forecast_quality`: good/fair/poor/error
- `sensor_price_quality`: good/fair/poor/insufficient/error
- `sensor_load_quality`: ml_prediction/historical/current_only/error

#### 📊 Better Monitoring

**Cost Metrics Available**
- Real-time charging cost tracking
- Savings vs average price calculation
- Optimization quality indicators
- Price comparison statistics

#### 🐛 Fixes

- Improved handling of missing sensors
- Better validation before sensor parsing
- More robust error recovery
- Enhanced logging context

#### 🔄 Migration

**Fully backward compatible** - No breaking changes
- All existing configurations work unchanged
- New cost sensor automatically added
- Enhanced optimization uses existing strategies
- No manual changes needed

---

### v2.3.0 (Dashboard & Configuration Improvements - November 2024)

#### 📊 Vylepšený Dashboard

**Nová sekce: Aktuální konfigurace**
- Zobrazení aktivní strategie nabíjení
- Aktuální SOC baterie v reálném čase
- Status test mode (ON/OFF)
- Čas příštího naplánovaného nabíjení
- Barevné indikátory stavu

**Data Status Panel**
- Přehled dostupnosti dat pro grafy
- Počet slotů v rozvrhu nabíjení
- Počet hodnot SOC forecastu
- Počet cenových bodů
- Počet hodnot solární predikce

**Rozšířený Test Mode**
- Detailní vysvětlení co je test mode
- Kdy a jak ho používat
- Co lze testovat
- Vizuální indikace stavu (oranžová/zelená)
- Seznam use cases pro testování

**Console Debugging**
- Automatické logování načtených dat
- Debug info pro inicializaci grafů
- Lepší error handling v SOC grafu
- Podpora pro null hodnoty (spanGaps)

#### ⚙️ Vylepšená Konfigurace

**Emoji Ikony**
- Vizuální identifikace každého pole
- Lepší orientace ve formuláři
- Konzistentní použití v celém UI

**Detailní Popisky**
- Vysvětlení každého parametru
- Doporučené hodnoty
- Příklady použití
- Formát dat a jednotky

**Multi-line Descriptions**
- Vysvětlení klíčových konceptů
- Hystereze a její účel
- Critical hours funkčnost
- ML predikce chování

**Kontextová Nápověda**
- Hints přímo v konfiguraci
- Tipy pro začátečníky
- Odkazy na další dokumentaci

#### 🔧 Technické Změny

**Branding Update**
- Výrobce změněn na "Martin Rak"
- Model: "Smart Battery Charging Controller"
- Firmware verze shodná s tag číslem (2.3.0)
- Konzistentní branding napříč UI

**Dokumentace**
- CHANGELOG.md pro HACS
- Rozšířené code comments
- Vylepšená hlavička coordinator.py
- Atribuce autora

**Dashboard Footer**
- Aktualizováno na v2.3.0
- Zobrazení autora (Martin Rak)
- Správný název produktu

#### 🐛 Debugging Improvements

**SOC Forecast Chart**
- Přidáno error logování
- Kontrola existence canvas elementu
- Validace dat před vykreslením
- SpanGaps pro lepší zobrazení

**Data Validation**
- Debug výpis počtu datových bodů
- Kontrola dostupnosti senzorů
- Logování prvních hodnot
- Error handling pro chybějící data

#### 📦 Migrace z v2.2.0

**Žádné breaking changes** - Plně kompatibilní
- Všechny existující konfigurace fungují beze změny
- Žádná nutná ruční migrace
- Pouze vizuální a UX vylepšení
- Dashboard automaticky použije nové features

**Doporučené akce po upgrade:**
1. Prohlédnout si novou sekci "Aktuální konfigurace"
2. Zkontrolovat Data Status panel
3. Vyzkoušet vylepšený test mode
4. Zkontrolovat console pro debug info (F12 v browseru)
5. Případně upravit konfiguraci s novými hinty

---

### v2.2.0 (Multi-Language, New Strategies & Charts - November 2024)

#### 🌍 Vícejazyčná podpora

**Kompletní podpora češtiny a angličtiny**
- Přepínání jazyka v konfiguraci integrace
- Přeložený dashboard a všechny UI elementy
- Lokalizované popisky grafů
- Automatické zapamatování preference

**Jak použít:**
- Nastavení → Zařízení a Služby → GW Smart Charging → KONFIGURACE
- Vyberte jazyk: "cs" (Čeština) nebo "en" (English)

#### 📊 Interaktivní grafy (Chart.js)

**3 nové živé grafy na dashboardu:**

1. **Graf cen a nabíjení**
   - Vizualizace cen elektřiny přes 24 hodin
   - Zelené značky ukazují plánované nabíjení
   - Interaktivní hover pro detaily

2. **Předpověď SOC**
   - Predikce stavu baterie na 24 hodin dopředu
   - Zobrazení 0-100% rozsahu
   - Gradient výplň pro lepší čitelnost

3. **Solární výroba**
   - Sloupcový graf očekávané produkce
   - Data v kWh pro každý 15min interval
   - Pomáhá plánovat nabíjení kolem slunce

**Výhody:**
- Responzivní design (mobil i desktop)
- Automatická aktualizace každých 15 minut
- Možnost stahování grafů jako obrázky
- Zoom a pan funkce

#### 🎯 4 nové strategie nabíjení

**6. Adaptivní chytrá**
- Učí se ze vzorců minulé spotřeby
- Kombinuje ML predikce s cenovou optimalizací
- Prioritizuje nabíjení před vysokou spotřebou
- Ideální pro uživatele s pravidelným režimem

**7. Priorita solární**
- Maximalizuje využití vlastní solární výroby
- Nabíjí především když je vysoká předpověď FV
- Minimální použití sítě
- Perfektní pro maximalizaci self-consumption

**8. Redukce špiček**
- Vyhýbá se síti během špičkových hodin
- Nabíjí v off-peak obdobích
- Snižuje náklady na poptávkové poplatky
- Konfiguruje se přes critical hours

**9. TOU optimalizace**
- Optimalizováno pro TOU tarify
- Automaticky detekuje cenové úrovně
- Nabíjí pouze v nejlevnější úrovni (40% rozsahu)
- Ideální pro víceúrovňové tarify

**Celkem 9 strategií:**
Dynamická, 4/6 nejlevnějších, Nanogreen, Cenový práh, Adaptivní, Solární, Redukce špiček, TOU

#### ⏱️ Celohodinové nabíjecí cykly

**Nová funkce: Full Hour Charging**
- Nabíjení v celých hodinových blocích
- 4 po sobě jdoucí 15min sloty = 1 hodina
- Lepší stabilita a ochrana baterie
- Stále analyzuje ceny po 15 minutách

**Výhody:**
- Konstantní hodinové vzorce nabíjení
- Méně přepínání nabíjení/vybíjení
- Lepší řízení cyklů baterie
- Konfigurovatelné (výchozí: zapnuto)

**Příklad:**
```
Před v2.2.0: Sloty 10:15, 14:00, 18:30, 22:45
Od v2.2.0:   Hodiny 22:00-23:00, 23:00-00:00, 01:00-02:00, 02:00-03:00
```

#### 📦 Aktualizace verzí

- manifest.json → 2.2.0
- Dashboard → 2.2.0 (hlavička i patička)
- Konzistentní zobrazování ve všech komponentách

#### 🔄 Migrace z v2.1.0

**Plně zpětně kompatibilní** - žádné breaking changes
- Všechny existující konfigurace fungují beze změny
- Výchozí strategie zůstává dynamická
- Výchozí jazyk: čeština
- Celohodinové nabíjení: zapnuto
- Není potřeba žádná ruční migrace

**Volitelná vylepšení po upgradu:**
1. Nastavit preferovaný jazyk
2. Vyzkoušet nové strategie
3. Prozkoumat nové grafy na dashboardu
4. Upravit full-hour charging podle potřeby

Více informací v `RELEASE_NOTES_v2.2.0.md`.

---

### v2.1.0 (Dashboard & Strategy Update - November 2024)

#### 🔧 Opravy kritických chyb

**Dashboard 24-Hour Prediction Plan**
- Opraven JSON parsing error při načítání 24h predikce
- Data jsou nyní embedována přímo v HTML z backendu
- Eliminovány problémy s autentizací API
- Rychlejší a spolehlivější načítání

**Tlačítka Aktivace/Deaktivace**
- Opravena nefunkční tlačítka ovládání integrace
- Přidána automatická autentizace pomocí tokenů
- Vizuální zpětná vazba o stavu tlačítek
- Automatické obnovení stránky po změně

#### ⚡ Vylepšení logiky nabíjení

**12-hodinový Lookahead**
- Změna z 24hodinového na **12hodinové** okno pro přesnější predikci
- **10% práh** pro detekci klesajících cen
- Čekání na minimum pouze pokud jsou nejlevnější ceny **alespoň 1 hodinu** v budoucnu
- Lepší porovnání aktuální vs budoucí průměrné ceny

#### 🎯 Strategie nabíjení (NOVÉ!)

**5 konfigurovatelných strategií:**

1. **Dynamická optimalizace** (výchozí)
   - Chytrá optimalizace na základě cen, předpovědí a ML vzorů
   - Čeká na nejlepší ceny při klesajícím trendu
   - Nejlepší pro maximální úspory

2. **4 nejlevnější hodiny**
   - Nabíjení vždy během 4 nejlevnějších hodin v příštích 24h
   - Jednoduché a předvídatelné
   - Vhodné pro běžné baterie

3. **6 nejlevnějších hodin**
   - Nabíjení během 6 nejlevnějších hodin
   - Více příležitostí k nabíjení
   - Vhodné pro větší baterie nebo spotřebu

4. **Pouze Nanogreen**
   - Používá pouze Nanogreen senzor pro rozhodování
   - Nabíjí když je `sensor.is_currently_in_five_cheapest_hours` ON
   - Pro uživatele důvěřující Nanogreen

5. **Cenový práh**
   - Nabíjí kdykoli cena klesne pod "Always Charge Price"
   - Nejagresivnější nabíjení
   - Vhodné pro velmi levné noční tarify

**Konfigurace:**
- Dostupné v průvodci nastavením
- Lze změnit přes Options Flow
- Plně zpětně kompatibilní (výchozí = dynamická)

#### 📦 Aktualizace verzí

- manifest.json → 2.1.0
- Dashboard → 2.1.0
- Lovelace Card → 2.1.0
- Konzistentní zobrazování verzí

#### 🔄 Migrace z v2.0.0

**Plně zpětně kompatibilní** - žádné breaking changes
- Všechny existující konfigurace fungují beze změny
- Výchozí strategie je dynamická (stejné chování jako v2.0)
- Není potřeba žádná ruční migrace

Více informací v `RELEASE_NOTES_v2.1.0.md`.

---

### v2.0.0 (Major Feature Release - November 2024)

#### 🆕 Nové funkce

**Nanogreen Integrace**
- Podpora pro `sensor.is_currently_in_five_cheapest_hours`
- Automatické nabíjení během 5 nejlevnějších hodin
- Inteligentní fallback na standardní logiku

**Pokročilé ML Vzory**
- Samostatné predikce pro pracovní dny (Po-Pá)
- Samostatné predikce pro víkendy (So-Ne)
- Samostatné predikce pro svátky
- Detekce českých svátků (11 hlavních svátků)
- Udržování 30denní historie pro každý typ dne

**Řízení Přídavných Spínačů**
- Podpora pro libovolné spínače z Home Assistantu
- Automatické zapínání/vypínání podle ceny elektřiny
- Konfigurovatelný cenový práh
- Nezávislé sledování stavu pro každý spínač
- Ideální pro bojlery, čerpadla, EV nabíječky

**Testovací Režim**
- Bezpečné testování bez skutečného ovládání
- Detailní logování plánovaných akcí
- Konfigurovatelné přes UI
- Vhodné pro ladění a testování nových konfigurací

#### 🐛 Opravy
- **Dashboard Error 500** - Opraven chybějící import `aiohttp.web` ve view.py
- Response třída nyní správně importována

#### 📝 Dokumentace
- **RELEASE_NOTES_v2.0.0.md** - Kompletní release notes s příklady
- **README.md** - Aktualizováno o nové funkce v2.0

#### 🔄 Migrace
- **Žádné breaking changes** - Plně zpětně kompatibilní s v1.9.5
- Všechny nové funkce volitelné
- Rekonfigurace přes Options Flow

Více informací v `RELEASE_NOTES_v2.0.0.md`.

### v1.8.0 (Entity Consolidation & Device Integration Release)

### Služba pro automatizace
Nová služba `gw_smart_charging.get_charging_schedule` poskytuje detailní informace o plánu nabíjení:
- Plánované periody nabíjení ze sítě
- Plánované periody vybíjení baterie
- Plánované periody nabíjení ze solárů
- Sloty s očekávaným importem ze sítě
- Denní statistiky (kWh, náklady)
- Real-time metriky baterie a sítě
- Informace o optimalizaci

### Nové senzory
- `sensor.gw_smart_charging_next_grid_charge` - Čas příštího nabíjení ze sítě
- `sensor.gw_smart_charging_next_battery_discharge` - Čas příštího vybíjení baterie
- `sensor.gw_smart_charging_activity_log` - Log změn režimů a aktivit

### Vylepšená optimalizace
- **Vážená ML predikce**: Novější dny mají větší vliv na predikci spotřeby
- **Chytřejší grid charging**: Rozhodování založené na budoucím deficitu energie
- **Respektování kapacity baterie**: Prevence přebíjení a zbytečných cyklů
- **Minimální prah nabíjení**: Nabíjí pouze pokud je potřeba > 0.5 kWh

Více informací v `FEATURE_SERVICE_v1.6.0.md`.

## Dokumentace

Detailní dokumentace je v `/custom_components/gw_smart_charging/README.md`

## Release Notes

### v1.8.0 (Entity Consolidation & Device Integration Release)
- 📱 **Device Panel** - Plná integrace do Zařízení a Služby v Home Assistentu
- 🎯 **Konsolidace entit** - Snížení z 21 na 10 entit pro lepší přehlednost
- 🔧 **Oprava diagnostiky** - Správné zobrazení aktuálního SoC v diagnostickém senzoru
- 📚 **Dokumentace logiky** - Nový soubor CHARGING_LOGIC.md s kompletním popisem
- 📊 **Série data v atributech** - Grafy dostupné v atributech `soc_forecast` senzoru
- 💡 **Lepší pochopitelnost** - Jasné názvy senzorů a jejich účel
- 🔄 **Migrace** - Data z odstraněných senzorů dostupná v konsolidovaných atributech
- ✨ **Device Info** - Všechny entity nyní mají device_info pro správné seskupení

### v1.7.0 (Autonomous Service & Statistics Release)
- 🤖 **Autonomní služba** - Integrace funguje plně autonomně bez zásahu uživatele
- 📊 **Nový sensor: Daily Statistics** - Denní statistiky nabíjení, úspory, efektivita
- 🔮 **Nový sensor: Prediction** - ML konfidence, kvalita predikce, forecast confidence
- 💸 **Savings tracking** - Výpočet úspor oproti pausálnímu tarifu
- 📈 **Funkční ApexCharts** - Opraven data_generator pro správné zobrazení grafů
- 🎨 **Nový Lovelace dashboard** - Kompletní dashboard s všemi novými senzory (lovelace_v1.7.0.yaml)
- 📋 **Efektivita nabíjení** - Porovnání plánovaného vs skutečného nabíjení
- 🔍 **Prediction quality score** - Celkový score kvality predikce (0-100)
- 📝 **Rozšířené senzory** - Všechny senzory zobrazují podrobné stavy a atributy
- ✨ **Ready for release** - Připraveno pro produkční nasazení

### v1.6.0 (Service & Enhanced Optimization Release)
- 🛠️ **Nová služba** - `get_charging_schedule` pro automatizace, skripty a scény
- 📝 **3 nové senzory** - next_grid_charge, next_battery_discharge, activity_log
- 🧠 **Vylepšená ML predikce** - Vážené průměrování s exponenciálním rozpadem
- 🔮 **Chytrá optimalizace** - Rozhodování založené na budoucí spotřebě a kapacitě baterie
- 📊 **Activity tracking** - Sledování změn režimů a stavu systému
- 📋 **Rozšířené příklady** - Nové automatizace využívající službu
- 🔧 **Lepší grid charging** - Výpočet energy deficitu pro optimální nabíjení

### v1.5.0 (Unit Conversion & Dashboard Release)
- 🔄 **W→kWh konverze** - Automatický převod výkonových senzorů (W) na energii (kWh) pro správnou logiku
- 📊 **Battery power sign handling** - Správné zpracování sensor.battery_power (+ = vybíjení, - = nabíjení)
- 📉 **Nové senzory** - Today's battery charge/discharge tracking v kWh
- 🎨 **Dashboard** - Nový přehledný dashboard podobný open-meteo integraci
- 📈 **Real-time metriky** - Rozšířená diagnostika s battery a grid metrikami v W i kWh
- 🔧 **Vylepšená konfigurace** - Podpora pro sensor.today_battery_charge a sensor.today_battery_discharge
- 📝 **Strings.json** - Přidány překlady pro lepší UI
- ✨ **Vylepšený diagnostický senzor** - Kompletní přehled včetně real-time battery status

### v1.4.0 (Active Automation Release)
- ✅ **Automatické řízení** - Integrace aktivně volá script.nabijeni_on/off každé 2 minuty
- 🔄 **Vyšší frekvence aktualizací** - Update interval snížen z 5 na 2 minuty pro rychlejší reakci
- 🎯 **Chytrá optimalizace** - Skripty se volají pouze při změně stavu (prevence zbytečných volání)
- 🔍 **Nový diagnostický senzor** - Kompletní přehled stavu, konfigurace a logiky integrace
- 📊 **Vylepšená data pro ApexCharts** - Optimalizovaný formát atributů pro grafování
- 📋 **Detailní logování** - Přesné informace o volání skriptů a režimech nabíjení
- 🔧 **Stabilní konfigurace** - Všechny senzory a skripty správně propojené

### v1.3.0 (Production Release)
- ✅ **Production Ready** - Kompletně otestovaná a stabilní verze
- 🔧 **Defaultní konfigurace** - Všechny senzory mají správné výchozí hodnoty
- 📋 **Kompletní dokumentace** - Mapování senzorů pro snadnou instalaci
- 🎯 **Optimalizovaná logika** - Hystereze, ML predikce, Critical hours
- 🔒 **Security** - 0 vulnerabilities (CodeQL verified)

### v1.2.0
- 🔄 **Hystereze** - ±5% buffer kolem cenových prahů pro prevenci oscilace
- 🧠 **ML Predikce** - Průměrování 30 denních vzorů spotřeby pro přesnější plánování
- ⏰ **Critical Hours** - Udržování vyššího SOC během peak hours (default 17-21)
- 📊 **Nové senzory** - battery_power, energy_buy (grid import)
- 🎯 **Smart režimy** - grid_charge_critical pro rozlišení peak hour charging

### v1.1.1
- ✨ 15minutové intervaly (96 slotů/den) místo hodinových
- 🎯 Cenové prahy: always_charge_price, never_charge_price
- 🔋 SOC limity: min/max/target pro ochranu baterie
- 📊 Nové senzory: Schedule, SOC Forecast, Series soc_forecast
- 🔄 Switch pro automatické řízení nabíjení
- 📈 Predikce spotřeby z daily load sensor
- 📝 Kompletní dokumentace včetně Lovelace příkladů

### v1.0.x
- Základní optimalizace nabíjení
- Hodinové plánování
- UI konfigurace
