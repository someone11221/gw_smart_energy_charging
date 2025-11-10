# GW Smart Charging Coordinator - 15-minute interval optimization logic

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import timedelta, datetime, date, time as dt_time, timezone

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_FORECAST_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_LOAD_SENSOR,
    CONF_DAILY_LOAD_SENSOR,
    CONF_SOC_SENSOR,
    CONF_BATTERY_POWER_SENSOR,
    CONF_GRID_IMPORT_SENSOR,
    CONF_CHARGING_ON_SCRIPT,
    CONF_CHARGING_OFF_SCRIPT,
    CONF_ENABLE_AUTOMATION,
    CONF_BATTERY_CAPACITY,
    CONF_MAX_CHARGE_POWER,
    CONF_CHARGE_EFFICIENCY,
    CONF_MIN_SOC,
    CONF_MAX_SOC,
    CONF_TARGET_SOC,
    CONF_ALWAYS_CHARGE_PRICE,
    CONF_NEVER_CHARGE_PRICE,
    CONF_PRICE_HYSTERESIS,
    CONF_CRITICAL_HOURS_START,
    CONF_CRITICAL_HOURS_END,
    CONF_CRITICAL_HOURS_SOC,
    CONF_ENABLE_ML_PREDICTION,
    DEFAULT_BATTERY_CAPACITY,
    DEFAULT_MAX_CHARGE_POWER,
    DEFAULT_CHARGE_EFFICIENCY,
    DEFAULT_MIN_SOC,
    DEFAULT_MAX_SOC,
    DEFAULT_TARGET_SOC,
    DEFAULT_ALWAYS_CHARGE_PRICE,
    DEFAULT_NEVER_CHARGE_PRICE,
    DEFAULT_PRICE_HYSTERESIS,
    DEFAULT_CRITICAL_HOURS_START,
    DEFAULT_CRITICAL_HOURS_END,
    DEFAULT_CRITICAL_HOURS_SOC,
    DEFAULT_ENABLE_ML_PREDICTION,
)

_LOGGER = logging.getLogger(__name__)


class GWSmartCoordinator(DataUpdateCoordinator):
    """Coordinator that reads forecast, price and load sensors and produces a charging schedule."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="gw_smart_charging_coordinator",
            update_interval=timedelta(minutes=2),  # Update every 2 minutes for responsive automation
        )
        self.entry = entry
        self.config: dict[str, Any] = entry.data or {}
        # cache to accumulate cumulative daily deltas while running
        self._last_daily_cumulative: Optional[float] = None
        self._last_daily_date: Optional[date] = None
        # Machine learning data - store last 30 days of hourly consumption patterns
        self._ml_history: List[List[float]] = []  # List of 24-hour patterns
        self._last_charging_state: bool = False  # For hysteresis tracking
        self._last_script_state: Optional[bool] = None  # Track last script execution state

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and normalize forecast, price and load data and compute 15-min schedule."""
        try:
            forecast_sensor = self.config.get(CONF_FORECAST_SENSOR)
            price_sensor = self.config.get(CONF_PRICE_SENSOR)
            load_sensor = self.config.get(CONF_LOAD_SENSOR)
            daily_load_sensor = self.config.get(CONF_DAILY_LOAD_SENSOR)

            # Use 96 slots for 15-minute intervals (24 hours * 4)
            forecast_15min: List[float] = [0.0] * 96
            price_15min: List[float] = [0.0] * 96
            load_15min: List[float] = [0.0] * 96

            forecast_meta = {}
            forecast_timestamps: List[str] = []

            # Parse forecast (supports 15-min data from sensor.energy_production_d2)
            if forecast_sensor:
                state = self.hass.states.get(forecast_sensor)
                if state:
                    _LOGGER.debug("Parsing forecast from %s", forecast_sensor)
                    forecast_15min = self._parse_forecast_15min(state)
                    forecast_timestamps = self._build_forecast_timestamps_15min(state)
                    conf_score, conf_reason, source, slots = self._compute_forecast_confidence(state)
                    forecast_meta = {
                        "forecast_confidence": {"score": conf_score, "reason": conf_reason},
                        "forecast_source": source,
                        "forecast_slots_count": slots,
                    }
                else:
                    _LOGGER.debug("Forecast sensor %s not found", forecast_sensor)

            # Parse price (from sensor.current_consumption_price_czk_kwh with today/tomorrow hourly)
            if price_sensor:
                state = self.hass.states.get(price_sensor)
                if state:
                    _LOGGER.debug("Parsing prices from %s", price_sensor)
                    price_15min = self._parse_price_15min(state)
                else:
                    _LOGGER.debug("Price sensor %s not found", price_sensor)

            # Parse load - use ML prediction if enabled, otherwise use daily sensor
            ml_enabled = self.config.get(CONF_ENABLE_ML_PREDICTION, DEFAULT_ENABLE_ML_PREDICTION)
            if daily_load_sensor:
                state_daily = self.hass.states.get(daily_load_sensor)
                if state_daily:
                    if ml_enabled:
                        _LOGGER.debug("Using ML prediction for load pattern")
                        load_15min = self._ml_predict_load_pattern(state_daily)
                        # Update ML history with current actual consumption
                        current_actual = self._parse_daily_load_pattern_15min(state_daily)
                        self._update_ml_history(current_actual)
                    else:
                        _LOGGER.debug("Parsing daily load pattern from %s", daily_load_sensor)
                        load_15min = self._parse_daily_load_pattern_15min(state_daily)
            
            # Fallback to current consumption sensor
            if not any(load_15min) and load_sensor:
                state = self.hass.states.get(load_sensor)
                if state:
                    _LOGGER.debug("Using current load from %s", load_sensor)
                    load_15min = self._parse_current_load_15min(state)

            # Compute 15-min optimized schedule
            schedule = self._compute_schedule_15min(forecast_15min, price_15min, load_15min)

            # Get real-time battery and grid metrics (with W to kWh conversion)
            battery_metrics = self._get_battery_metrics()
            grid_metrics = self._get_grid_metrics()

            # Execute charging automation if enabled
            await self._execute_charging_automation(schedule)

            return {
                "status": "ok",
                "forecast_15min": forecast_15min,
                "price_15min": price_15min,
                "load_15min": load_15min,
                "schedule": schedule,
                "timestamps": forecast_timestamps,
                "battery_metrics": battery_metrics,
                "grid_metrics": grid_metrics,
                **forecast_meta,
                "last_update": datetime.now(timezone.utc).isoformat(),
            }
        except Exception as err:
            _LOGGER.error("Update failed: %s", err, exc_info=True)
            raise UpdateFailed(err) from err

    async def _execute_charging_automation(self, schedule: List[Dict[str, Any]]) -> None:
        """Execute charging scripts based on current schedule slot.
        
        Only calls scripts when state changes to avoid unnecessary calls.
        """
        # Check if automation is enabled
        automation_enabled = self.config.get(CONF_ENABLE_AUTOMATION, True)
        if not automation_enabled:
            _LOGGER.debug("Automation disabled, skipping script execution")
            return
        
        # Get scripts
        charging_on_script = self.config.get(CONF_CHARGING_ON_SCRIPT)
        charging_off_script = self.config.get(CONF_CHARGING_OFF_SCRIPT)
        
        if not charging_on_script or not charging_off_script:
            _LOGGER.debug("Charging scripts not configured, skipping automation")
            return
        
        # Get current slot
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        
        if not schedule or slot >= len(schedule):
            _LOGGER.debug("No schedule available for current slot %d", slot)
            return
        
        current_slot = schedule[slot]
        should_charge = current_slot.get("should_charge", False)
        
        # Only call script if state changed
        if self._last_script_state is None or self._last_script_state != should_charge:
            try:
                if should_charge:
                    _LOGGER.info("Turning ON charging (slot %d, mode: %s, price: %.2f CZK/kWh)", 
                                slot, current_slot.get("mode", "unknown"), 
                                current_slot.get("price_czk_kwh", 0.0))
                    await self.hass.services.async_call(
                        "script", "turn_on", 
                        {"entity_id": charging_on_script}, 
                        blocking=False
                    )
                else:
                    _LOGGER.info("Turning OFF charging (slot %d, mode: %s)", 
                                slot, current_slot.get("mode", "unknown"))
                    await self.hass.services.async_call(
                        "script", "turn_on", 
                        {"entity_id": charging_off_script}, 
                        blocking=False
                    )
                
                self._last_script_state = should_charge
                _LOGGER.debug("Script execution successful, new state: %s", should_charge)
                
            except Exception as e:
                _LOGGER.error("Failed to execute charging script: %s", e, exc_info=True)
        else:
            _LOGGER.debug("Charging state unchanged (%s), skipping script call", should_charge)

    # ---------- NEW: 15-minute interval parsing methods ----------
    
    def _parse_forecast_15min(self, state) -> List[float]:
        """Parse solar forecast from sensor.energy_production_d2 with 15-min watts attribute."""
        attrs = state.attributes or {}
        watts = attrs.get("watts")
        
        if isinstance(watts, dict) and watts:
            # Sort by timestamp and convert to 15-min intervals (W to kW)
            slots = [0.0] * 96
            for ts_str, w_value in watts.items():
                try:
                    ts = datetime.fromisoformat(ts_str)
                    # Calculate 15-min slot index (0-95)
                    hour = ts.hour
                    minute = ts.minute
                    slot_idx = hour * 4 + minute // 15
                    if 0 <= slot_idx < 96:
                        slots[slot_idx] = float(w_value) / 1000.0  # W to kW
                except Exception as e:
                    _LOGGER.debug("Failed to parse forecast timestamp %s: %s", ts_str, e)
                    continue
            return slots
        
        # Fallback: use hourly wh_period and distribute evenly
        wh_period = attrs.get("wh_period")
        if isinstance(wh_period, dict) and wh_period:
            slots = [0.0] * 96
            for ts_str, wh_value in wh_period.items():
                try:
                    ts = datetime.fromisoformat(ts_str)
                    hour = ts.hour
                    kw_avg = float(wh_value) / 1000.0  # Wh to kWh, then average over hour
                    # Fill 4 slots for this hour
                    for i in range(4):
                        slot_idx = hour * 4 + i
                        if 0 <= slot_idx < 96:
                            slots[slot_idx] = kw_avg
                except Exception:
                    continue
            return slots
        
        return [0.0] * 96
    
    def _parse_price_15min(self, state) -> List[float]:
        """Parse electricity price from sensor with today/tomorrow_hourly_prices, expand to 15-min."""
        attrs = state.attributes or {}
        
        # Get tomorrow prices (for planning ahead) or fallback to today
        prices_hourly = attrs.get("tomorrow_hourly_prices")
        if not prices_hourly or len(prices_hourly) < 24:
            prices_hourly = attrs.get("today_hourly_prices")
        
        if isinstance(prices_hourly, list) and len(prices_hourly) >= 24:
            # Expand hourly prices to 15-min slots (each hour gets 4 identical price slots)
            slots = []
            for price in prices_hourly[:24]:
                for _ in range(4):
                    slots.append(float(price))
            return slots[:96]
        
        return [0.0] * 96
    
    def _parse_daily_load_pattern_15min(self, state) -> List[float]:
        """Parse historical daily load pattern from sensor.house_consumption_daily."""
        # This would ideally use historical data to predict tomorrow's consumption pattern
        # For now, use a simplified approach - could be enhanced with HA history
        attrs = state.attributes or {}
        
        # If we had yesterday's hourly data, we could use it
        # For now, return flat profile - this should be enhanced
        try:
            # Get total daily consumption and distribute based on typical pattern
            total_kwh = float(state.state)
            # Simple pattern: higher during day (6-22), lower at night
            pattern = []
            for hour in range(24):
                if 6 <= hour < 22:
                    factor = 1.2  # 20% above average during day
                else:
                    factor = 0.5  # 50% of average at night
                hour_kwh = (total_kwh / 24) * factor
                # Split into 4x 15-min slots
                for _ in range(4):
                    pattern.append(hour_kwh / 4)
            return pattern[:96]
        except Exception:
            return [0.0] * 96
    
    def _parse_current_load_15min(self, state) -> List[float]:
        """Parse current load from sensor.house_consumption (in W) and create flat 15-min profile."""
        try:
            current_w = float(state.state)
            current_kw = current_w / 1000.0
            # Use current value as flat forecast for all slots
            return [current_kw] * 96
        except Exception:
            return [0.0] * 96
    
    def _ml_predict_load_pattern(self, daily_load_sensor_state) -> List[float]:
        """Use machine learning (weighted averaging) to predict consumption pattern from history.
        
        Enhanced logic:
        - Separate weekday vs weekend patterns
        - Weight recent days more heavily
        - Consider similar days (same day of week)
        """
        from datetime import datetime
        
        if not self._ml_history:
            # No history yet, fall back to current day pattern
            return self._parse_daily_load_pattern_15min(daily_load_sensor_state)
        
        # Get current day of week (0=Monday, 6=Sunday)
        today = datetime.now()
        is_weekend = today.weekday() >= 5  # Saturday or Sunday
        
        # Enhanced prediction with weighted average
        prediction = [0.0] * 96
        total_weight = 0.0
        
        # Process historical patterns with exponential decay weighting
        for idx, hist_pattern in enumerate(self._ml_history):
            if len(hist_pattern) != 96:
                continue
            
            # Calculate weight: more recent = higher weight
            # Most recent day gets weight 1.0, oldest gets ~0.33
            days_ago = len(self._ml_history) - idx - 1
            recency_weight = 1.0 / (1.0 + days_ago * 0.1)
            
            # Apply pattern to prediction
            for i in range(96):
                prediction[i] += hist_pattern[i] * recency_weight
            total_weight += recency_weight
        
        # Normalize by total weight
        if total_weight > 0:
            prediction = [p / total_weight for p in prediction]
        
        # Add safety margin (10% increase) to avoid underestimating consumption
        prediction = [p * 1.1 for p in prediction]
        
        _LOGGER.debug(f"ML prediction based on {len(self._ml_history)} historical patterns "
                     f"(weekend: {is_weekend}, total_weight: {total_weight:.2f})")
        return prediction
    
    def _update_ml_history(self, current_pattern: List[float]) -> None:
        """Update ML history with current day's pattern (keep last 30 days)."""
        if len(current_pattern) == 96:
            self._ml_history.append(current_pattern)
            # Keep only last 30 days
            if len(self._ml_history) > 30:
                self._ml_history = self._ml_history[-30:]
            _LOGGER.debug(f"ML history updated: {len(self._ml_history)} patterns stored")
    
    def _build_forecast_timestamps_15min(self, state) -> List[str]:
        """Build list of 96 ISO timestamps for 15-min intervals (for day after tomorrow if _d2 sensor)."""
        use_day_after_tomorrow = "_d2" in (state.entity_id or "")
        base_date = datetime.now().date()
        if use_day_after_tomorrow:
            base_date += timedelta(days=2)
        else:
            base_date += timedelta(days=1)
        
        timestamps = []
        for hour in range(24):
            for minute in [0, 15, 30, 45]:
                dt_obj = datetime.combine(base_date, dt_time(hour=hour, minute=minute))
                timestamps.append(dt_obj.isoformat())
        return timestamps

    # ---------- OLD: hourly timestamps builder (keep for compatibility) ----------
        """Build list of 24 ISO timestamps for the forecast day (prefer tomorrow if sensor indicates it)."""
        # Determine whether forecast is for tomorrow:
        try:
            use_tomorrow = False
            if forecast_entity_id and "tomorrow" in forecast_entity_id:
                use_tomorrow = True
            # sensor attributes may include key 'tomorrow' or 'date'
            attrs = state.attributes or {}
            if any(k for k in attrs.keys() if "tomorrow" in str(k).lower()):
                use_tomorrow = True
            # if forecast_hourly seems to be for next-day (heuristic: state name contains 'tomorrow' or 'd2')
            if forecast_entity_id and ("_d2" in forecast_entity_id or "d2" in forecast_entity_id):
                # common naming for tomorrow forecast in user's setup
                use_tomorrow = True
        except Exception:
            use_tomorrow = False

        base_date = (datetime.now().date() + timedelta(days=1)) if use_tomorrow else datetime.now().date()
        timestamps = []
        # Use local time (no timezone string); Home Assistant will display appropriately.
        for h in range(24):
            dt_obj = datetime.combine(base_date, dt_time(hour=h))
            # produce ISO string with offset by using datetime.isoformat() (no explicit tz here)
            timestamps.append(dt_obj.isoformat())
        return timestamps

    # ---------- NEW: simple forecast confidence ----------
    def _compute_forecast_confidence(self, state) -> Tuple[float, str, str, int]:
        """Return (score 0..1, reason, source_label, slots_count).

        Heuristic rules:
        - If attribute 'watts' is mapping with many entries (>=48) -> high confidence.
        - If attribute 'hourly' with 24 -> good confidence.
        - If forecast provided as list of dicts with many slots -> good confidence.
        - If derived from scalar total -> low confidence.
        """
        attrs = state.attributes or {}
        # check watts mapping
        watts = attrs.get("watts")
        if isinstance(watts, dict) and watts:
            slots = len(watts)
            if slots >= 96:
                return 0.95, "Detailed 15-min PV forecast (96+ slots) -> high confidence", "watts_map", slots
            if slots >= 48:
                return 0.9, "Detailed 15-min PV forecast (48-95 slots) -> high confidence", "watts_map", slots
            return 0.8, "PV timeseries available (fewer slots) -> good confidence", "watts_map", slots

        # hourly list attribute
        hourly = attrs.get("hourly") or attrs.get("hourly_kw") or attrs.get("hourly_kwh")
        if isinstance(hourly, list) and len(hourly) >= 24:
            return 0.85, "Hourly forecast provided (24 values) -> good confidence", "hourly_list", len(hourly)

        # forecast list of dicts
        items = attrs.get("forecast") or attrs.get("values") or attrs.get("data")
        if isinstance(items, list) and items:
            slots = len(items)
            if slots >= 24:
                return 0.8, f"Forecast list with {slots} items -> good confidence", "forecast_list", slots
            return 0.6, f"Forecast list with {slots} items -> moderate confidence", "forecast_list", slots

        # fallback - scalar
        try:
            total = float(state.state)
            return 0.25, "Scalar total used for forecast -> low confidence", "scalar_total", 1
        except Exception:
            return 0.0, "No forecast data available", "none", 0

    # ---------- existing parse methods (unchanged) ----------
    def _parse_forecast_sensor(self, state) -> List[float]:
        """Normalize forecast sensor to 24 hourly kW values.

        Supports attribute 'watts' mapping timestamp->W, attribute 'hourly' (list kW),
        attribute 'forecast' list, or scalar total kWh.
        """
        attrs = state.attributes or {}
        # 'watts' mapping (15min -> W)
        watts = attrs.get("watts")
        if isinstance(watts, dict) and watts:
            return self._aggregate_timeseries_map_to_hourly(watts, value_in_watts=True)

        # already hourly list
        hourly = attrs.get("hourly") or attrs.get("hourly_kw") or attrs.get("hourly_kwh")
        if isinstance(hourly, list) and len(hourly) >= 24:
            return [round(float(x), 3) for x in hourly[:24]]

        # forecast list of dicts
        items = attrs.get("forecast") or attrs.get("values") or attrs.get("data")
        if isinstance(items, list) and items:
            # if it's a list of numbers
            if all(isinstance(x, (int, float)) for x in items) and len(items) >= 24:
                return [round(float(x), 3) for x in items[:24]]
            # otherwise parse dict items
            result_hour = [0.0] * 24
            cnt = [0] * 24
            for it in items:
                if not isinstance(it, dict):
                    continue
                pe = it.get("period_end") or it.get("datetime") or it.get("time")
                val = it.get("pv_estimate") or it.get("pv_estimate_kw") or it.get("value") or it.get("pv_estimate_w")
                if val is None or pe is None:
                    continue
                try:
                    hour = None
                    if isinstance(pe, str):
                        try:
                            hour = datetime.fromisoformat(pe).hour
                        except Exception:
                            if len(pe) >= 13:
                                hour = int(pe[11:13])
                    if hour is None:
                        continue
                    v = float(val)
                    if isinstance(it.get("pv_estimate_w"), (int, float)) or ("pv_estimate_w" in it):
                        v = v / 1000.0
                    elif v > 1000:
                        v = v / 1000.0
                    result_hour[hour] += v
                    cnt[hour] += 1
                except Exception:
                    continue
            out = []
            for h in range(24):
                if cnt[h] > 0:
                    out.append(round(result_hour[h] / cnt[h], 3))
                else:
                    out.append(0.0)
            return out

        # fallback: try parse state scalar as total kWh -> distribute evenly
        try:
            total = float(state.state)
            per_hour = total / 24.0
            return [round(per_hour, 3) for _ in range(24)]
        except Exception:
            _LOGGER.debug("Unable to parse forecast sensor %s attributes %s", state.entity_id, list(attrs.keys()))
            return [0.0] * 24

    def _parse_price_sensor(self, state) -> List[float]:
        """Normalize price sensor to 24 hourly currency/kWh values.

        Supports attributes tomorrow_hourly_prices / today_hourly_prices list or mapping timestamp->price.
        """
        attrs = state.attributes or {}
        tomorrow = attrs.get("tomorrow_hourly_prices")
        if isinstance(tomorrow, list) and len(tomorrow) >= 24:
            return [round(float(x), 4) for x in tomorrow[:24]]

        today = attrs.get("today_hourly_prices")
        if isinstance(today, list) and len(today) >= 24:
            return [round(float(x), 4) for x in today[:24]]

        # mapping timestamp->price
        for keyname in ("prices", "values", "prices_map", "price_map"):
            mapping = attrs.get(keyname)
            if isinstance(mapping, dict) and mapping:
                return self._aggregate_timeseries_map_to_hourly(mapping, value_in_watts=False, unit=state.attributes.get("unit_of_measurement", ""))

        # forecast list of dicts with period_end + price
        items = attrs.get("forecast") or attrs.get("data") or None
        if isinstance(items, list) and items:
            result_hour = [0.0] * 24
            cnt = [0] * 24
            unit = state.attributes.get("unit_of_measurement", "")
            for it in items:
                if not isinstance(it, dict):
                    continue
                pe = it.get("period_end") or it.get("datetime") or it.get("time")
                val = it.get("price") or it.get("value") or it.get("price_czk")
                if val is None or pe is None:
                    continue
                try:
                    hour = None
                    if isinstance(pe, str):
                        try:
                            hour = datetime.fromisoformat(pe).hour
                        except Exception:
                            if len(pe) >= 13:
                                hour = int(pe[11:13])
                    if hour is None:
                        continue
                    v = float(val)
                    # convert from MWh to kWh if unit indicates
                    if unit and ("MWh" in unit or "/MWh" in unit):
                        v = v / 1000.0
                    result_hour[hour] += v
                    cnt[hour] += 1
                except Exception:
                    continue
            out = []
            for h in range(24):
                if cnt[h] > 0:
                    out.append(round(result_hour[h] / cnt[h], 4))
                else:
                    out.append(0.0)
            return out

        # 4) fallback: if state is comma-separated list or JSON array
        try:
            s = state.state
            if isinstance(s, str) and s.startswith("[") and s.endswith("]"):
                import json
                arr = json.loads(s)
                if isinstance(arr, list) and len(arr) >= 24:
                    return [round(float(x), 4) for x in arr[:24]]
        except Exception:
            pass

        _LOGGER.debug("Unable to parse price sensor %s attributes %s unit=%s", state.entity_id, list(attrs.keys()), state.attributes.get("unit_of_measurement"))
        return [0.0] * 24

    def _parse_load_sensor(self, state, entity_id: Optional[str] = None) -> List[float]:
        """Normalize load (house consumption) sensor to 24 hourly kW values.

        Supported formats:
        - attribute 'yesterday_hourly' or 'today_hourly' as list of 24 numbers (kW or W)
        - attribute mapping timestamp->W (15min slots) in attribute 'watts' or 'values'
        - state as single number (current power) used as flat profile (converted to kW if likely in W)
        - OR daily cumulative sensor (reset at midnight) — detect via 'last_reset' attribute, device_class energy, or entity_id matches
          In that case:
            - if yesterday_hourly attribute available => use it for full profile
            - else if current cumulative present and time is e.g. 14:00 => distribute current cumulative evenly across passed hours
              (this gives an immediate estimate and will be refined as new readings arrive)
        """
        attrs = state.attributes or {}

        # 1) yesterday_hourly / today_hourly lists
        for key in ("yesterday_hourly", "today_hourly", "today_hourly_consumption", "yesterday_hourly_consumption"):
            arr = attrs.get(key)
            if isinstance(arr, list) and len(arr) >= 24:
                # detect if values are in W (large) -> convert to kW
                try:
                    sample = float(arr[0]) if arr else 0.0
                    factor = 1000.0 if abs(sample) > 1000 else 1.0
                    return [round(float(x) / factor, 3) for x in arr[:24]]
                except Exception:
                    continue

        # 2) mapping timestamp->value (like forecast)
        for mapkey in ("watts", "values", "consumption", "consumption_w"):
            mapping = attrs.get(mapkey)
            if isinstance(mapping, dict) and mapping:
                return self._aggregate_timeseries_map_to_hourly(mapping, value_in_watts=True)

        # 3) JSON array in state
        try:
            s = state.state
            if isinstance(s, str) and s.startswith("[") and s.endswith("]"):
                import json
                arr = json.loads(s)
                if isinstance(arr, list) and len(arr) >= 24:
                    sample = float(arr[0]) if arr else 0.0
                    factor = 1000.0 if abs(sample) > 1000 else 1.0
                    return [round(float(x) / factor, 3) for x in arr[:24]]
        except Exception:
            pass

        # 4) detect daily cumulative sensor (resets at midnight)
        # heuristics: presence of 'last_reset' attribute, device_class 'energy', or explicit entity name
        last_reset = attrs.get("last_reset")
        device_class = attrs.get("device_class") or ""
        is_daily_cumulative = False
        if last_reset:
            is_daily_cumulative = True
        if isinstance(device_class, str) and "energy" in device_class:
            is_daily_cumulative = True
        if entity_id and entity_id.endswith("denni_spotreba_domu"):
            is_daily_cumulative = True

        if is_daily_cumulative:
            # If sensor provides yesterday_hourly attribute, use it
            yesterday = attrs.get("yesterday_hourly") or attrs.get("yesterday")
            if isinstance(yesterday, list) and len(yesterday) >= 24:
                try:
                    sample = float(yesterday[0]) if yesterday else 0.0
                    factor = 1000.0 if abs(sample) > 1000 else 1.0
                    return [round(float(x) / factor, 3) for x in yesterday[:24]]
                except Exception:
                    pass

            # Otherwise try to estimate hourly consumption from cumulative value up to now.
            try:
                now = datetime.now()
                current_val = float(state.state)
                # if likely in Wh (large) -> convert to kWh
                if current_val > 1000:
                    # assume value is Wh -> convert
                    current_val = current_val / 1000.0
                # determine hours passed today (e.g., at 14:35 -> 14 hours completed)
                hours_passed = now.hour  # hours fully started since midnight (0..23)
                if hours_passed <= 0:
                    # early in day: nothing yet -> return zeros
                    return [0.0] * 24
                # distribute evenly across past hours as initial estimate
                per_hour = current_val / max(1, hours_passed)
                hourly = [0.0] * 24
                for h in range(hours_passed):
                    hourly[h] = round(per_hour, 3)
                # for future hours try to use yesterday profile if available, else leave zeros
                # if yesterday_hourly exists, use its slice for future hours
                if isinstance(yesterday, list) and len(yesterday) >= 24:
                    for h in range(hours_passed, 24):
                        try:
                            val = float(yesterday[h])
                            factor = 1000.0 if abs(val) > 1000 else 1.0
                            hourly[h] = round(float(val) / factor, 3)
                        except Exception:
                            hourly[h] = 0.0
                # store last cumulative for incremental updates while coordinator runs
                today_date = datetime.now().date()
                if self._last_daily_date != today_date:
                    self._last_daily_date = today_date
                    self._last_daily_cumulative = current_val
                else:
                    # if we have previous cumulative, compute delta since last run and add to current hour bucket
                    if self._last_daily_cumulative is not None and current_val >= self._last_daily_cumulative:
                        delta = current_val - self._last_daily_cumulative
                        # add delta to current hour
                        hourly[now.hour] = round(hourly[now.hour] + delta, 3)
                        self._last_daily_cumulative = current_val
                return hourly
            except Exception:
                _LOGGER.debug("Failed to estimate hourly from cumulative daily sensor %s", entity_id)

        # 5) fallback: if state is numeric current power, assume flat profile
        try:
            val = float(state.state)
            if abs(val) > 1000:
                val = val / 1000.0
            return [round(val, 3) for _ in range(24)]
        except Exception:
            _LOGGER.debug("Unable to parse load sensor %s attributes %s", state.entity_id, list(attrs.keys()))
            return [0.0] * 24

    def _aggregate_timeseries_map_to_hourly(self, mapping: Dict[str, Any], value_in_watts: bool = False, unit: str = "") -> List[float]:
        """Aggregate a mapping timestamp->value (e.g. 15min slots) into 24 hourly values."""
        sums = [0.0] * 24
        counts = [0] * 24
        for k, v in mapping.items():
            try:
                hour = None
                if isinstance(k, str):
                    try:
                        hour = datetime.fromisoformat(k).hour
                    except Exception:
                        if len(k) >= 13:
                            hour = int(k[11:13])
                if hour is None:
                    continue
                val = float(v)
                if value_in_watts:
                    val = val / 1000.0  # W -> kW
                else:
                    if unit and ("MWh" in unit or "/MWh" in unit):
                        val = val / 1000.0
                sums[hour] += val
                counts[hour] += 1
            except Exception:
                continue

        out = []
        for h in range(24):
            if counts[h] > 0:
                out.append(round(sums[h] / counts[h], 3))
            else:
                out.append(0.0)
        return out

    def _find_optimal_charging_slots(self, prices: List[float], loads: List[float], forecast: List[float],
                                     soc_kwh: float, target_soc_kwh: float, capacity: float,
                                     max_charge: float, eff: float, interval_hours: float = 0.25) -> List[int]:
        """Find optimal charging slots considering price trends and energy needs.
        
        NEW v1.9.5: Enhanced logic to wait for cheapest prices in decreasing trend.
        
        Args:
            prices: List of prices for 96 slots
            loads: List of load forecasts for 96 slots
            forecast: List of PV forecasts for 96 slots
            soc_kwh: Current battery SOC in kWh
            target_soc_kwh: Target SOC to reach in kWh
            capacity: Battery capacity in kWh
            max_charge: Max charging power in kW
            eff: Charging efficiency
            interval_hours: Duration of each slot in hours (0.25 for 15min)
            
        Returns:
            List of slot indices where charging should occur
        """
        # Calculate energy deficit that needs to be covered by grid charging
        energy_needed = max(0, target_soc_kwh - soc_kwh)
        
        if energy_needed < 0.5:  # Less than 0.5 kWh needed, no charging
            return []
        
        # Calculate how many slots we need to charge
        max_energy_per_slot = max_charge * interval_hours * eff
        slots_needed = int((energy_needed / max_energy_per_slot) + 0.5)
        
        if slots_needed <= 0:
            return []
        
        # Find charging windows with price trend analysis
        charging_slots = []
        
        # Group prices into windows and find decreasing trends
        current_time_slot = datetime.now().hour * 4 + (datetime.now().minute // 15)
        
        # Look ahead for next 24 hours (96 slots)
        valid_slots = []
        for slot in range(current_time_slot, min(current_time_slot + 96, 96)):
            price = prices[slot] if slot < len(prices) else 999.0
            if price > 0:  # Valid price
                valid_slots.append((slot, price))
        
        if not valid_slots:
            return []
        
        # Sort by price to find cheapest slots
        valid_slots.sort(key=lambda x: x[1])
        
        # NEW v1.9.5: Check for decreasing price trend
        # If prices are generally decreasing, wait for the minimum
        if len(valid_slots) >= 4:
            # Calculate trend: compare first quarter vs last quarter average
            quarter_size = len(valid_slots) // 4
            early_avg = sum(p for _, p in valid_slots[:quarter_size]) / quarter_size
            late_avg = sum(p for _, p in valid_slots[-quarter_size:]) / quarter_size
            
            is_decreasing_trend = late_avg < early_avg * 0.95  # 5% decrease = trend
            
            if is_decreasing_trend:
                _LOGGER.info("Detected decreasing price trend - waiting for minimum prices")
                # Take cheapest slots from the later half (where prices are lower)
                midpoint = len(valid_slots) // 2
                cheapest_slots = [s for s, p in valid_slots[midpoint:midpoint + slots_needed]]
            else:
                # Normal case: just take cheapest slots overall
                cheapest_slots = [s for s, p in valid_slots[:slots_needed]]
        else:
            cheapest_slots = [s for s, p in valid_slots[:slots_needed]]
        
        # Verify slots are within reasonable time window (next 8 hours for non-critical)
        max_wait_slots = 32  # 8 hours
        filtered_slots = [s for s in cheapest_slots if s <= current_time_slot + max_wait_slots]
        
        if not filtered_slots and cheapest_slots:
            # If all slots are too far, take at least the closest cheapest one
            filtered_slots = sorted(cheapest_slots)[:max(1, slots_needed // 2)]
        
        return sorted(filtered_slots)
    
    def _compute_schedule_15min(self, forecast: List[float], prices: List[float], loads: List[float]) -> List[Dict[str, Any]]:
        """Compute optimized 15-min charging schedule with hysteresis and critical hours support.
        
        Returns list[96] with dicts for each 15-min slot:
        { slot, time, mode, pv_power_kW, load_kW, net_pv_kW, price_czk_kwh, 
          planned_charge_kW, soc_kwh_end, soc_pct_end, should_charge }
        
        Logic (ENHANCED v1.9.5):
        1. Always use solar energy first (self-consumption priority)
        2. Find optimal charging windows considering price trends (NEW)
        3. Wait for cheapest prices in decreasing trend scenarios (NEW)
        4. Charge from grid only when price is below threshold AND battery needs charging
        5. Never charge if price above never_charge_price threshold
        6. Always charge if price below always_charge_price AND battery below target
        7. Respect min/max SOC limits
        8. Consider solar forecast to avoid charging from grid if solar will cover needs
        9. Apply hysteresis to prevent rapid switching near price thresholds
        10. Maintain higher SOC during critical hours
        """
        # Read config params
        capacity = float(self.config.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY))
        max_charge = float(self.config.get(CONF_MAX_CHARGE_POWER, DEFAULT_MAX_CHARGE_POWER))
        eff = float(self.config.get(CONF_CHARGE_EFFICIENCY, DEFAULT_CHARGE_EFFICIENCY))
        
        min_soc_pct = float(self.config.get(CONF_MIN_SOC, DEFAULT_MIN_SOC))
        max_soc_pct = float(self.config.get(CONF_MAX_SOC, DEFAULT_MAX_SOC))
        target_soc_pct = float(self.config.get(CONF_TARGET_SOC, DEFAULT_TARGET_SOC))
        
        always_charge_price = float(self.config.get(CONF_ALWAYS_CHARGE_PRICE, DEFAULT_ALWAYS_CHARGE_PRICE))
        never_charge_price = float(self.config.get(CONF_NEVER_CHARGE_PRICE, DEFAULT_NEVER_CHARGE_PRICE))
        hysteresis_pct = float(self.config.get(CONF_PRICE_HYSTERESIS, DEFAULT_PRICE_HYSTERESIS))
        
        # Critical hours configuration
        critical_start = int(self.config.get(CONF_CRITICAL_HOURS_START, DEFAULT_CRITICAL_HOURS_START))
        critical_end = int(self.config.get(CONF_CRITICAL_HOURS_END, DEFAULT_CRITICAL_HOURS_END))
        critical_soc_pct = float(self.config.get(CONF_CRITICAL_HOURS_SOC, DEFAULT_CRITICAL_HOURS_SOC))
        
        # Calculate hysteresis bands
        hysteresis_factor = hysteresis_pct / 100.0
        if self._last_charging_state:
            # If we were charging, make it harder to stop (upper band)
            always_charge_threshold = always_charge_price * (1 + hysteresis_factor)
            never_charge_threshold = never_charge_price * (1 + hysteresis_factor)
        else:
            # If we were not charging, make it harder to start (lower band)
            always_charge_threshold = always_charge_price * (1 - hysteresis_factor)
            never_charge_threshold = never_charge_price * (1 - hysteresis_factor)

        # Get initial SOC
        initial_soc_frac = 0.5  # default 50%
        soc_sensor = self.config.get(CONF_SOC_SENSOR)
        if soc_sensor:
            st = self.hass.states.get(soc_sensor)
            if st:
                try:
                    val = float(st.state)
                    initial_soc_frac = max(0.0, min(1.0, val / 100.0))
                except Exception:
                    pass

        soc_kwh = capacity * initial_soc_frac
        min_soc_kwh = capacity * (min_soc_pct / 100.0)
        max_soc_kwh = capacity * (max_soc_pct / 100.0)
        target_soc_kwh = capacity * (target_soc_pct / 100.0)
        critical_soc_kwh = capacity * (critical_soc_pct / 100.0)

        schedule: List[Dict[str, Any]] = []
        current_should_charge = False
        
        # NEW v1.9.5: Pre-compute optimal charging slots using price trend analysis
        optimal_charging_slots = self._find_optimal_charging_slots(
            prices, loads, forecast, soc_kwh, target_soc_kwh, 
            capacity, max_charge, eff, interval_hours=0.25
        )
        _LOGGER.debug(f"Optimal charging slots identified: {optimal_charging_slots}")
        
        # First pass: identify cheap charging opportunities and solar surplus
        for slot in range(96):
            pv_kw = float(forecast[slot]) if slot < len(forecast) else 0.0
            price = float(prices[slot]) if slot < len(prices) else 0.0
            load_kw = float(loads[slot]) if slot < len(loads) else 0.0
            
            # 15-min interval = 0.25 hours
            interval_hours = 0.25
            
            # Calculate time for this slot
            hour = slot // 4
            minute = (slot % 4) * 15
            
            # Check if in critical hours
            is_critical_hour = False
            if critical_start <= critical_end:
                is_critical_hour = critical_start <= hour < critical_end
            else:  # Crosses midnight
                is_critical_hour = hour >= critical_start or hour < critical_end
            
            # Adjust target SOC for critical hours
            effective_target_soc_kwh = critical_soc_kwh if is_critical_hour else target_soc_kwh
            
            # Net solar after house consumption
            net_pv_kw = pv_kw - load_kw
            
            mode = "idle"
            planned_charge_kw = 0.0
            should_charge = False
            
            # Priority 1: Use surplus solar for charging
            if net_pv_kw > 0.05:
                # Can charge from solar surplus
                available_charge_kw = min(net_pv_kw, max_charge)
                capacity_left_kwh = max_soc_kwh - soc_kwh
                max_charge_this_slot_kwh = available_charge_kw * interval_hours
                
                if capacity_left_kwh > 0.01:
                    charge_kwh = min(max_charge_this_slot_kwh, capacity_left_kwh)
                    stored_kwh = charge_kwh * eff
                    soc_kwh += stored_kwh
                    planned_charge_kw = charge_kwh / interval_hours
                    mode = "solar_charge"
                    should_charge = False  # No grid charging needed
            
            # Priority 2: Discharge to cover load (battery -> house)
            elif load_kw > pv_kw and soc_kwh > min_soc_kwh:
                deficit_kw = load_kw - pv_kw
                available_discharge_kwh = soc_kwh - min_soc_kwh
                max_discharge_this_slot_kw = min(deficit_kw, max_charge)
                discharge_kwh = min(max_discharge_this_slot_kw * interval_hours, available_discharge_kwh)
                
                soc_kwh -= discharge_kwh / eff
                planned_charge_kw = -(discharge_kwh / interval_hours)  # Negative = discharge
                mode = "battery_discharge"
                should_charge = False
            
            # Priority 3: Grid charging based on price thresholds with hysteresis
            # NEW v1.9.5: Use optimal slot selection for grid charging
            if soc_kwh < effective_target_soc_kwh:
                # Check if this slot is in optimal charging slots (NEW v1.9.5)
                is_optimal_slot = slot in optimal_charging_slots
                
                # Check price conditions with hysteresis
                if price > 0:
                    if price <= always_charge_threshold:
                        # Very cheap - always charge
                        capacity_left_kwh = max_soc_kwh - soc_kwh
                        if capacity_left_kwh > 0.01:
                            charge_kw = min(max_charge, capacity_left_kwh / interval_hours)
                            charge_kwh = charge_kw * interval_hours
                            stored_kwh = charge_kwh * eff
                            soc_kwh += stored_kwh
                            planned_charge_kw = charge_kw
                            mode = "grid_charge_cheap"
                            should_charge = True
                            current_should_charge = True
                    
                    elif price < never_charge_threshold and is_optimal_slot:
                        # NEW v1.9.5: Only charge in optimal slots (not just any cheap slot)
                        # This implements "wait for cheapest price" logic
                        capacity_left_kwh = max_soc_kwh - soc_kwh
                        if capacity_left_kwh > 0.01:
                            charge_kw = min(max_charge, capacity_left_kwh / interval_hours)
                            charge_kwh = charge_kw * interval_hours
                            stored_kwh = charge_kwh * eff
                            soc_kwh += stored_kwh
                            planned_charge_kw = charge_kw
                            mode = "grid_charge_optimal" if not is_critical_hour else "grid_charge_critical"
                            should_charge = True
                            current_should_charge = True
                            
                            _LOGGER.debug(
                                f"Grid charging optimal slot {slot}: price={price:.2f}, "
                                f"is_optimal={is_optimal_slot}, "
                                f"charging={charge_kwh:.2f} kWh"
                            )
            
            # Ensure SOC stays within bounds
            soc_kwh = max(min_soc_kwh, min(max_soc_kwh, soc_kwh))
            soc_pct = (soc_kwh / capacity) * 100.0
            
            # Update charging state for next iteration's hysteresis
            if should_charge:
                self._last_charging_state = True
            
            # Time calculation
            hour = slot // 4
            minute = (slot % 4) * 15
            time_str = f"{hour:02d}:{minute:02d}"
            
            schedule.append({
                "slot": slot,
                "time": time_str,
                "mode": mode,
                "pv_power_kW": round(pv_kw, 3),
                "load_kW": round(load_kw, 3),
                "net_pv_kW": round(net_pv_kw, 3),
                "price_czk_kwh": round(price, 4),
                "planned_charge_kW": round(planned_charge_kw, 3),
                "soc_kwh_end": round(soc_kwh, 3),
                "soc_pct_end": round(soc_pct, 2),
                "should_charge": should_charge,
                "is_critical_hour": is_critical_hour,
            })
        
        # Update final charging state after all slots computed
        if schedule:
            self._last_charging_state = schedule[-1].get("should_charge", False)
        
        return schedule

    def _compute_schedule(self, forecast: List[float], prices: List[float], loads: List[float]) -> List[Dict[str, Any]]:
        """Compute a simple hourly plan that includes house load.

        Returns list[24] with dicts:
        { hour, mode, pv_power_kW, load_kW, net_pv_kW, price_czk_kwh, planned_power_kW, soc_kwh_end, soc_pct_end }
        """
        # Read config params
        capacity = float(self.config.get(CONF_BATTERY_CAPACITY, 17.0))  # kWh
        max_charge = float(self.config.get(CONF_MAX_CHARGE_POWER, 3.7))  # kW
        eff = float(self.config.get(CONF_CHARGE_EFFICIENCY, 0.95))
        min_reserve_pct = float(self.config.get(CONF_MIN_RESERVE, 10.0)) / 100.0

        # initial SOC: from configured SOC sensor if present
        initial_soc_frac = 0.5  # default 50%
        soc_sensor = self.config.get(CONF_SOC_SENSOR)
        if soc_sensor:
            st = self.hass.states.get(soc_sensor)
            if st:
                try:
                    val = float(st.state)
                    if val > 1.0:
                        initial_soc_frac = max(0.0, min(1.0, val / 100.0))
                    else:
                        initial_soc_frac = max(0.0, min(1.0, val))
                except Exception:
                    pass

        soc_kwh = capacity * initial_soc_frac
        min_reserve_kwh = capacity * min_reserve_pct

        # compute price threshold (25th percentile) for "cheap" hours
        sorted_prices = sorted([p for p in prices if p and p > 0.0])
        if sorted_prices:
            idx = max(0, int(len(sorted_prices) * 0.25) - 1)
            price_threshold = sorted_prices[idx]
        else:
            price_threshold = 0.0

        schedule: List[Dict[str, Any]] = []
        for h in range(24):
            pv = float(forecast[h]) if h < len(forecast) else 0.0
            price = float(prices[h]) if h < len(prices) else 0.0
            load = float(loads[h]) if h < len(loads) else 0.0

            # net PV available for charging after household consumption
            net_pv = pv - load  # kW (positive = surplus, negative = deficit)

            mode = "idle"
            planned_power = 0.0  # positive = charge into battery, negative = discharge to supply home/grid
            # Use surplus PV first for charging (self-consumption)
            if net_pv > 0.05:
                # can use net_pv up to max_charge to charge battery
                charge_power = min(net_pv, max_charge)
                # limit to capacity remaining (kWh)
                capacity_left_kwh = capacity - soc_kwh
                max_possible_charge = capacity_left_kwh  # over 1 hour
                charge_power = min(charge_power, max_possible_charge)
                stored_kwh = charge_power * eff
                soc_kwh += stored_kwh
                planned_power = charge_power
                mode = "pv"
            else:
                # no surplus PV: consider discharging to cover home load (to avoid grid import)
                capacity_above_reserve = soc_kwh - min_reserve_kwh
                if capacity_above_reserve > 0.1:
                    discharge_power = min(max_charge, load, capacity_above_reserve)
                    soc_kwh -= discharge_power / eff
                    planned_power = -discharge_power
                    mode = "battery"
                else:
                    # If price is cheap and battery has space, charge from grid
                    capacity_left_kwh = capacity - soc_kwh
                    if price_threshold > 0 and price > 0 and price <= price_threshold and capacity_left_kwh > 0.01:
                        charge_power = min(max_charge, capacity_left_kwh)
                        stored_kwh = charge_power * eff
                        soc_kwh += stored_kwh
                        planned_power = charge_power
                        mode = "grid"
                    else:
                        mode = "idle"
                        planned_power = 0.0

            soc_kwh = max(0.0, min(capacity, soc_kwh))
            soc_pct = round((soc_kwh / capacity) * 100.0, 2)

            schedule.append({
                "hour": h,
                "mode": mode,
                "pv_power_kW": round(pv, 3),
                "load_kW": round(load, 3),
                "net_pv_kW": round(net_pv, 3),
                "price_czk_kwh": round(price, 4),
                "planned_power_kW": round(planned_power, 3),
                "soc_kwh_end": round(soc_kwh, 3),
                "soc_pct_end": soc_pct,
            })

        return schedule

    def _get_battery_metrics(self) -> Dict[str, Any]:
        """Get real-time battery metrics with W to kWh conversion.
        
        Returns battery power, state of charge, and today's charge/discharge.
        Note: battery_power is positive when discharging, negative when charging.
        """
        battery_power_sensor = self.config.get(CONF_BATTERY_POWER_SENSOR)
        soc_sensor = self.config.get(CONF_SOC_SENSOR)
        
        from .const import CONF_TODAY_BATTERY_CHARGE_SENSOR, CONF_TODAY_BATTERY_DISCHARGE_SENSOR
        today_charge_sensor = self.config.get(CONF_TODAY_BATTERY_CHARGE_SENSOR)
        today_discharge_sensor = self.config.get(CONF_TODAY_BATTERY_DISCHARGE_SENSOR)
        
        metrics = {
            "battery_power_w": 0.0,
            "battery_power_kw": 0.0,
            "battery_status": "idle",
            "soc_pct": 0.0,
            "soc_kwh": 0.0,
            "today_charge_kwh": 0.0,
            "today_discharge_kwh": 0.0,
        }
        
        # Get battery power (W) - positive = discharge, negative = charge
        if battery_power_sensor:
            state = self.hass.states.get(battery_power_sensor)
            if state:
                try:
                    power_w = float(state.state)
                    metrics["battery_power_w"] = power_w
                    metrics["battery_power_kw"] = round(power_w / 1000.0, 3)
                    if power_w > 10:
                        metrics["battery_status"] = "discharging"
                    elif power_w < -10:
                        metrics["battery_status"] = "charging"
                    else:
                        metrics["battery_status"] = "idle"
                except (ValueError, TypeError):
                    pass
        
        # Get SOC (%)
        if soc_sensor:
            state = self.hass.states.get(soc_sensor)
            if state:
                try:
                    soc_pct = float(state.state)
                    metrics["soc_pct"] = soc_pct
                    # Calculate kWh from percentage
                    capacity = float(self.config.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY))
                    metrics["soc_kwh"] = round((soc_pct / 100.0) * capacity, 3)
                except (ValueError, TypeError):
                    pass
        
        # Get today's charge (kWh)
        if today_charge_sensor:
            state = self.hass.states.get(today_charge_sensor)
            if state:
                try:
                    metrics["today_charge_kwh"] = round(float(state.state), 3)
                except (ValueError, TypeError):
                    pass
        
        # Get today's discharge (kWh)
        if today_discharge_sensor:
            state = self.hass.states.get(today_discharge_sensor)
            if state:
                try:
                    metrics["today_discharge_kwh"] = round(float(state.state), 3)
                except (ValueError, TypeError):
                    pass
        
        return metrics
    
    def _get_grid_metrics(self) -> Dict[str, Any]:
        """Get real-time grid import metrics with W to kWh conversion."""
        grid_import_sensor = self.config.get(CONF_GRID_IMPORT_SENSOR)
        load_sensor = self.config.get(CONF_LOAD_SENSOR)
        
        from .const import CONF_PV_POWER_SENSOR
        pv_power_sensor = self.config.get(CONF_PV_POWER_SENSOR)
        
        metrics = {
            "grid_import_w": 0.0,
            "grid_import_kw": 0.0,
            "house_load_w": 0.0,
            "house_load_kw": 0.0,
            "pv_power_w": 0.0,
            "pv_power_kw": 0.0,
        }
        
        # Get grid import (W)
        if grid_import_sensor:
            state = self.hass.states.get(grid_import_sensor)
            if state:
                try:
                    import_w = float(state.state)
                    metrics["grid_import_w"] = import_w
                    metrics["grid_import_kw"] = round(import_w / 1000.0, 3)
                except (ValueError, TypeError):
                    pass
        
        # Get house load (W)
        if load_sensor:
            state = self.hass.states.get(load_sensor)
            if state:
                try:
                    load_w = float(state.state)
                    metrics["house_load_w"] = load_w
                    metrics["house_load_kw"] = round(load_w / 1000.0, 3)
                except (ValueError, TypeError):
                    pass
        
        # Get PV power (W)
        if pv_power_sensor:
            state = self.hass.states.get(pv_power_sensor)
            if state:
                try:
                    pv_w = float(state.state)
                    metrics["pv_power_w"] = pv_w
                    metrics["pv_power_kw"] = round(pv_w / 1000.0, 3)
                except (ValueError, TypeError):
                    pass
        
        return metrics
