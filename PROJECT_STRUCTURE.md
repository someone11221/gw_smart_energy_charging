# Struktura projektu - Smart Battery Charging v3.0.1

```
gw_smart_charging_v3/
├── custom_components/
│   └── gw_smart_charging/
│       ├── __init__.py                          # Main integration setup
│       ├── manifest.json                         # Integration metadata
│       ├── const.py                              # Constants and defaults
│       ├── config_flow.py                        # UI configuration flow
│       ├── coordinator.py                        # Main coordinator (orchestration)
│       ├── sensor.py                             # Sensor platform (6 sensors)
│       ├── switch.py                             # Switch platform (auto-charging)
│       ├── views.py                              # API views for dashboard
│       ├── services.yaml                         # Service definitions
│       │
│       ├── price_providers/                      # Price provider modules
│       │   ├── __init__.py
│       │   ├── base.py                          # Abstract base class
│       │   ├── ote.py                           # OTE (Czech market)
│       │   └── nanogreen.py                     # Nanogreen integration
│       │
│       ├── battery_controllers/                  # Battery controller modules
│       │   ├── __init__.py
│       │   ├── base.py                          # Abstract base class
│       │   └── goodwe.py                        # GoodWe implementation
│       │
│       ├── charging_strategies/                  # Charging strategy modules
│       │   ├── __init__.py
│       │   └── intelligent.py                   # Intelligent strategy with peak prediction
│       │
│       ├── ml_models/                            # ML models (future)
│       │   └── __init__.py
│       │
│       ├── ui/                                   # Dashboard UI
│       │   ├── __init__.py
│       │   └── dashboard.html                   # Modern dashboard with Chart.js
│       │
│       └── translations/                         # Localization
│           ├── cs.json                          # Czech
│           └── en.json                          # English
│
├── README.md                                     # Main documentation
├── CHANGELOG.md                                  # Version history
├── INSTALLATION.md                               # Installation guide
├── LICENSE                                       # MIT License
├── hacs.json                                     # HACS metadata
└── info.md                                       # HACS info page
```

## Klíčové komponenty

### Core Files

**`__init__.py`**
- Setup integrace
- Registrace platforem (sensor, switch)
- Registrace služeb
- Registrace dashboard views

**`coordinator.py`**
- Centrální orchestrace všech komponent
- Update cycle každé 2 minuty
- Vytváření a aktualizace charging plánu
- Rozhodování o spuštění/zastavení nabíjení

**`config_flow.py`**
- 3-krokový UI průvodce konfigurací
- Options flow pro změnu parametrů
- Validace vstupů

### Price Providers

**`price_providers/base.py`**
- Abstract base class `PriceProvider`
- Data classes: `PricePoint`, `PriceForecast`
- Společné metody: `get_current_price()`, `get_forecast()`

**`price_providers/ote.py`**
- Implementace pro český OTE trh
- Parsování `today_hourly_prices` a `tomorrow_hourly_prices`
- Automatická konverze na `PriceForecast`

**`price_providers/nanogreen.py`**
- Integrace s Nanogreen sensorem
- Podpora `is_currently_in_five_cheapest_hours`

### Battery Controllers

**`battery_controllers/base.py`**
- Abstract base class `BatteryController`
- Data class: `BatteryStatus`
- Společné metody: `start_charging()`, `stop_charging()`, `get_status()`

**`battery_controllers/goodwe.py`**
- Implementace pro GoodWe systémy
- Správné zpracování power sensoru (+ = discharge, - = charge)
- Volání charging skriptů

### Charging Strategy

**`charging_strategies/intelligent.py`**
- **IntelligentChargingStrategy** - hlavní třída
- Data classes: `ChargingSlot`, `ChargingPlan`
- Algoritmy:
  - `_identify_peaks()` - detekce cenových špiček
  - `_identify_cheap_slots()` - výběr nejlevnějších slotů
  - `create_charging_plan()` - vytvoření optimálního plánu
  - `should_charge_now()` - rozhodnutí o nabíjení

### Platforms

**`sensor.py`**
6 senzorů:
1. `battery_status` - SOC, power, charging/discharging
2. `charging_plan` - sloty, peaky, náklady
3. `price_forecast` - ceny 24-48h, min/max/avg
4. `next_charging` - další plánované nabíjení
5. `statistics` - confidence, metrika kvality
6. `diagnostics` - system info, debug data

**`switch.py`**
1 switch:
- `auto_charging` - zapnutí/vypnutí automatiky

### Dashboard

**`ui/dashboard.html`**
- Modern single-page HTML dashboard
- Chart.js grafy (ceny, SOC predikce)
- Real-time monitoring
- Control panel (enable/disable, refresh)
- Responsive design

**`views.py`**
API endpoints:
- `/api/gw_smart_charging/dashboard` - HTML dashboard
- `/api/gw_smart_charging/data` - JSON data pro dashboard
- `/api/gw_smart_charging/enable_auto` - zapnutí auto-charging
- `/api/gw_smart_charging/disable_auto` - vypnutí auto-charging
- `/api/gw_smart_charging/refresh_plan` - force plan update

## Data Flow

```
┌─────────────────────────────────────────────────────────────┐
│                      Coordinator (2min cycle)                │
│                                                               │
│  1. Update price provider → PriceForecast                   │
│  2. Update battery controller → BatteryStatus               │
│  3. Create charging plan (every 15min)                       │
│     └─ IntelligentChargingStrategy                          │
│        ├─ Identify peaks (48h)                              │
│        ├─ Identify cheap slots                              │
│        ├─ Plan peak preparation                             │
│        ├─ Plan opportunistic full charging                  │
│        └─ Apply safety rules                                │
│  4. Execute charging decision                                │
│     └─ should_charge_now() → start/stop charging            │
│                                                               │
└─────────────────────────────────────────────────────────────┘
                              │
                              ↓
                    ┌──────────────────────┐
                    │   Update entities     │
                    │  - 6 sensors          │
                    │  - 1 switch           │
                    └──────────────────────┘
                              │
                              ↓
                    ┌──────────────────────┐
                    │   Dashboard views     │
                    │  - Serve HTML         │
                    │  - Provide JSON data  │
                    └──────────────────────┘
```

## Extensibility

### Adding new price provider

1. Create `price_providers/myprovider.py`
2. Extend `PriceProvider` base class
3. Implement `async_update()`, `get_current_price()`, `get_forecast()`
4. Add to `PRICE_PROVIDERS` in `config_flow.py`
5. Update `coordinator.py` initialization

### Adding new battery controller

1. Create `battery_controllers/mybattery.py`
2. Extend `BatteryController` base class
3. Implement `async_update()`, `start_charging()`, `stop_charging()`
4. Add to `BATTERY_TYPES` in `config_flow.py`
5. Update `coordinator.py` initialization

### Adding new charging strategy

1. Create `charging_strategies/mystrategy.py`
2. Implement `create_charging_plan()` method
3. Add strategy selection in config flow
4. Update coordinator to use selected strategy

## Performance Considerations

- **Update interval**: 2 minutes (configurable in coordinator)
- **Plan recalculation**: Every 15 minutes
- **Price forecast**: 24-48 hours cached
- **Battery status**: Real-time from sensors
- **Dashboard refresh**: 60 seconds (client-side)

## Security

- Dashboard requires Home Assistant authentication
- No external API calls (all local)
- Scripts executed in HA context
- No sensitive data stored

## Future Enhancements

See `ml_models/` directory for planned features:
- Machine learning consumption prediction
- Pattern recognition (workday/weekend/holiday)
- Weather-based solar forecast integration
- Multi-battery support
- EV charging integration

---

**Version**: 3.0.1  
**Author**: Martin Rak  
**License**: MIT
