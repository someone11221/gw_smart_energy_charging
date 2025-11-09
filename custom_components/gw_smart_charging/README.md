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
- **SOC limity**: Min/Max/Target pro ochranu a optimální využití baterie
- **Predikce spotřeby**: Využití historických dat pro přesnější plánování
- **Automatické ovládání**: Switch pro zapínání/vypínání nabíjení podle plánu

## Senzory

Integration vytváří následující senzory:

- **GW Smart Charging Forecast** - Solární forecast (15min data)
- **GW Smart Charging Price** - Ceny elektřiny (15min data)
- **GW Smart Charging Schedule** - Aktuální režim a plán nabíjení
- **GW Smart Charging SOC Forecast** - Predikce stavu baterie
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
- **soc_sensor**: sensor.battery_state_of_charge (battery SOC %)
- **goodwe_switch**: switch.nabijeni_ze_site (charging control)

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

### Automatizace
- **enable_automation**: Povolit automatické ovládání switche
- **switch_on_means_charge**: Switch ON = nabíjení

## Rekonfigurace

Pro změnu senzorů nebo parametrů:
1. Settings → Devices & Services → GW Smart Charging
2. Klikněte na "Configure" (ikona ozubeného kola)
3. Upravte požadované hodnoty a uložte

Integration se automaticky znovu načte s novými nastaveními.

## Lovelace vizualizace

Pro zobrazení grafů použijte ApexCharts card nebo podobné s atributy `data_15min` a `timestamps` ze series senzorů.

Příklad ApexCharts konfigurace:
```yaml
type: custom:apexcharts-card
graph_span: 24h
span:
  start: day
header:
  show: true
  title: Plán nabíjení
series:
  - entity: sensor.gw_smart_charging_series_pv
    name: Solární výroba
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  - entity: sensor.gw_smart_charging_series_load
    name: Spotřeba domu
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
  - entity: sensor.gw_smart_charging_series_battery_charge
    name: Nabíjení baterie
    data_generator: |
      return entity.attributes.data_15min.map((value, index) => {
        return [new Date(entity.attributes.timestamps[index]).getTime(), value];
      });
```
