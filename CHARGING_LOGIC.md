# GW Smart Charging - Charging Logic Documentation

## Overview
GW Smart Charging is an intelligent battery charging controller for Home Assistant that optimizes when to charge your GoodWe battery based on solar forecast, electricity prices, and consumption patterns. The system makes decisions every 15 minutes (96 intervals per day) to maximize solar self-consumption and minimize electricity costs.

## Sensors Used

### Required Input Sensors
1. **`sensor.energy_production_d2`** - Solar forecast sensor
   - Provides 15-minute PV forecast in Watts
   - Automatically converted to kW for calculations
   - Used to predict solar energy availability

2. **`sensor.current_consumption_price_czk_kwh`** - Electricity price sensor
   - Provides current and forecast prices in CZK/kWh
   - Has attributes: `today_hourly_prices`, `tomorrow_hourly_prices`
   - Converted from hourly to 15-minute resolution
   - Used for price-based charging decisions

3. **`sensor.house_consumption`** - Current house consumption
   - Real-time consumption in Watts
   - Automatically converted to kW
   - Used as fallback for consumption prediction

4. **`sensor.house_consumption_daily`** - Daily consumption history
   - Total daily consumption in kWh
   - Used for ML consumption prediction
   - Builds 30-day historical pattern database

5. **`sensor.battery_state_of_charge`** - Battery State of Charge
   - Current battery level in percentage (0-100%)
   - Used to calculate available capacity
   - Critical for SOC forecast calculations

6. **`sensor.battery_power`** - Real-time battery power
   - Power in Watts (positive = discharging, negative = charging)
   - Used for monitoring battery status
   - Provides charging/discharging state

### Optional Sensors
7. **`sensor.energy_buy`** - Grid import sensor
   - Monitors power imported from grid (W)
   - Used for real-time grid import tracking

8. **`sensor.today_battery_charge`** - Today's battery charge
   - Total energy charged into battery today (kWh)
   - Used for efficiency calculations

9. **`sensor.today_battery_discharge`** - Today's battery discharge
   - Total energy discharged from battery today (kWh)
   - Used for efficiency calculations

10. **`sensor.pv_power`** - Current PV production
    - Real-time solar panel output (W)
    - Used for current production monitoring

### Control Scripts
- **`script.nabijeni_on`** - Script to enable grid charging
- **`script.nabijeni_off`** - Script to disable grid charging

## Charging Decision Logic

### 1. Data Collection Phase (Every 2 Minutes)
The coordinator collects and processes data:

```
┌─────────────────────────────────────────────────────┐
│ STEP 1: Collect Sensor Data                        │
│ - Solar forecast (96 x 15-min slots)               │
│ - Electricity prices (96 x 15-min slots)           │
│ - Consumption prediction (96 x 15-min slots)       │
│ - Current battery SOC                              │
└─────────────────────────────────────────────────────┘
```

### 2. ML-Based Consumption Prediction
If enabled, the system uses machine learning to predict consumption:

```python
# Weighted averaging of last 30 days
# Recent days have higher weight (exponential decay)
for historical_pattern in last_30_days:
    weight = 1.0 / (1.0 + days_ago * 0.1)
    prediction += pattern * weight

# Add 10% safety margin
prediction *= 1.1
```

### 3. Optimization Loop (96 15-Minute Slots)
For each 15-minute slot, the system:

```
FOR each 15-min slot (0-95):
    ┌──────────────────────────────────────────┐
    │ Calculate Energy Balance                 │
    │ pv_kwh = forecast[slot] * 0.25h         │
    │ load_kwh = predicted_load[slot] * 0.25h │
    │ net_pv = pv_kwh - load_kwh              │
    └──────────────────────────────────────────┘
    
    ┌──────────────────────────────────────────┐
    │ Determine Charging Mode                  │
    │ IF price < always_charge_threshold:      │
    │   → GRID_CHARGE (cheap electricity)      │
    │ ELIF price > never_charge_threshold:     │
    │   → NO_CHARGE (expensive electricity)    │
    │ ELIF net_pv > 0:                         │
    │   → SOLAR_CHARGE (excess solar)          │
    │ ELIF is_critical_hour AND soc < target: │
    │   → GRID_CHARGE_CRITICAL (peak prep)     │
    │ ELIF future_deficit > 0.5 kWh:           │
    │   → GRID_CHARGE (smart charging)         │
    │ ELSE:                                    │
    │   → BATTERY_DISCHARGE or SELF_CONSUME    │
    └──────────────────────────────────────────┘
    
    ┌──────────────────────────────────────────┐
    │ Update Battery SOC Forecast              │
    │ soc_kwh[slot+1] = soc_kwh[slot]         │
    │                   + charge_kwh           │
    │                   - discharge_kwh        │
    │ Respect: min_soc ≤ soc ≤ max_soc        │
    └──────────────────────────────────────────┘
```

### 4. Charging Modes Explained

#### a) **SOLAR_CHARGE** 
- When: Excess solar production (PV > Load)
- Action: Charge battery from solar surplus
- Cost: FREE (using own solar)

#### b) **GRID_CHARGE**
- When: Price < always_charge_threshold (default 1.5 CZK/kWh)
- Action: Charge battery from grid
- Cost: Low electricity price

#### c) **GRID_CHARGE_CRITICAL**
- When: Critical hours (default 17-21) AND SOC < critical_soc
- Action: Ensure battery charged for evening peak
- Cost: May charge at higher price to ensure availability

#### d) **BATTERY_DISCHARGE**
- When: High prices AND battery available
- Action: Use battery to avoid expensive grid import
- Savings: Avoid expensive electricity

#### e) **SELF_CONSUME**
- When: Normal operation with sufficient solar/battery
- Action: Use solar + battery as needed
- Cost: Minimal grid import

#### f) **NO_CHARGE**
- When: Price > never_charge_threshold (default 4.0 CZK/kWh)
- Action: Never charge from grid (too expensive)
- Alternative: Wait for cheaper prices or solar

### 5. Price Hysteresis
To prevent oscillation around thresholds:

```python
# ±5% buffer around price thresholds
if currently_charging:
    stop_if_price > threshold * (1 + hysteresis/100)
else:
    start_if_price < threshold * (1 - hysteresis/100)
```

### 6. Smart Grid Charging Decision
The system looks ahead to determine if grid charging is needed:

```python
# Calculate future energy deficit
future_deficit = 0
for future_slot in remaining_day:
    if net_pv[slot] < 0:  # Consumption > Production
        future_deficit += abs(net_pv[slot])

# Charge if deficit > 0.5 kWh and price is reasonable
if future_deficit > 0.5 and price < average_price:
    mode = GRID_CHARGE
```

## Configuration Parameters

### Battery Configuration
- **`battery_capacity_kwh`** (default: 17.0)
  - Total battery capacity in kWh
  
- **`max_charge_power_kw`** (default: 3.7)
  - Maximum charging/discharging power in kW
  
- **`charge_efficiency`** (default: 0.95)
  - Battery charging efficiency (95%)
  - Accounts for conversion losses

### SOC Limits
- **`min_soc_pct`** (default: 10%)
  - Minimum allowed battery level (protection)
  
- **`max_soc_pct`** (default: 95%)
  - Maximum allowed battery level (protection)
  
- **`target_soc_pct`** (default: 90%)
  - Target SOC for optimization

### Price Thresholds
- **`always_charge_price`** (default: 1.5 CZK/kWh)
  - Below this price, always charge if needed
  
- **`never_charge_price`** (default: 4.0 CZK/kWh)
  - Above this price, never charge from grid
  
- **`price_hysteresis_pct`** (default: 5%)
  - Buffer to prevent oscillation around thresholds

### Critical Hours
- **`critical_hours_start`** (default: 17)
  - Start of peak demand hours (17:00)
  
- **`critical_hours_end`** (default: 21)
  - End of peak demand hours (21:00)
  
- **`critical_hours_soc_pct`** (default: 80%)
  - Desired SOC during critical hours

### ML Prediction
- **`enable_ml_prediction`** (default: False)
  - Enable machine learning consumption prediction
  - Uses last 30 days of consumption patterns
  - Weighted averaging with exponential decay

## Output Sensors

### Core Sensors
1. **`sensor.gw_smart_charging_forecast`**
   - Current value: Peak solar forecast (kW)
   - Attributes: 15-min forecast, prices, schedule
   
2. **`sensor.gw_smart_charging_schedule`**
   - Current value: Current charging mode
   - Attributes: Full schedule, next charge times
   
3. **`sensor.gw_smart_charging_soc_forecast`**
   - Current value: Forecasted SOC (%)
   - Attributes: SOC forecast array, series data for charts
   
4. **`sensor.gw_smart_charging_battery_power`**
   - Current value: Battery power (W)
   - Attributes: SoC, today's charge/discharge totals

### Information Sensors
5. **`sensor.gw_smart_charging_diagnostics`**
   - Current value: Integration status with current SOC
   - Attributes: All config, metrics, status info
   
6. **`sensor.gw_smart_charging_daily_statistics`**
   - Current value: Planned grid charge (kWh)
   - Attributes: Daily stats, efficiency, savings
   
7. **`sensor.gw_smart_charging_prediction`**
   - Current value: ML prediction quality
   - Attributes: Confidence scores, forecast quality
   
8. **`sensor.gw_smart_charging_next_charge`**
   - Current value: Next grid charge time
   - Attributes: All charging/discharging periods
   
9. **`sensor.gw_smart_charging_activity_log`**
   - Current value: Current activity
   - Attributes: Mode changes, activity history

### Switch
10. **`switch.gw_smart_charging_auto_charging`**
    - Controls: Automatic charging on/off
    - Follows schedule automatically

## Example Scenario

### Morning (6:00-9:00)
```
Time: 06:00, Price: 2.0 CZK/kWh, SOC: 45%
- Solar forecast: 0.5 kW (sunrise starting)
- Load: 1.0 kW (morning consumption)
- Decision: GRID_CHARGE (price < threshold)
→ Charge battery while price is low

Time: 08:00, Price: 3.5 CZK/kWh, SOC: 75%
- Solar forecast: 3.0 kW (sunny)
- Load: 1.2 kW
- Net PV: +1.8 kW (surplus)
- Decision: SOLAR_CHARGE
→ Store solar surplus in battery
```

### Midday (11:00-14:00)
```
Time: 12:00, Price: 4.5 CZK/kWh, SOC: 95%
- Solar forecast: 5.0 kW (peak production)
- Load: 0.8 kW
- Net PV: +4.2 kW (large surplus)
- Decision: SELF_CONSUME
→ Battery full, use solar directly, export surplus
```

### Evening (17:00-21:00)
```
Time: 18:00, Price: 5.5 CZK/kWh, SOC: 82%
- Solar forecast: 0.2 kW (sunset)
- Load: 2.5 kW (peak consumption)
- Critical hour: YES
- Decision: BATTERY_DISCHARGE
→ Use battery to avoid expensive grid import
→ Battery was prepared during cheaper hours
```

### Night (22:00-5:00)
```
Time: 23:00, Price: 1.8 CZK/kWh, SOC: 35%
- Solar forecast: 0 kW
- Load: 0.5 kW
- Future deficit: 8 kWh (for tomorrow)
- Decision: GRID_CHARGE
→ Recharge battery at night rate
→ Prepare for tomorrow's consumption
```

## Benefits
- ✅ **Cost Savings**: Charge when prices are low, discharge when high
- ✅ **Solar Maximization**: Prioritize solar self-consumption
- ✅ **Peak Preparation**: Ensure battery ready for evening demand
- ✅ **Smart Forecasting**: ML-based consumption prediction
- ✅ **Automatic Operation**: Fully autonomous every 2 minutes
- ✅ **Safety Limits**: Protects battery with SOC limits
- ✅ **Hysteresis**: Prevents frequent mode switching
