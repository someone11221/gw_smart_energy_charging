# Updated coordinator: adds ISO timestamps for target day and a simple forecast confidence metric.

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import timedelta, datetime, date, time as dt_time

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_FORECAST_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_LOAD_SENSOR,
    CONF_SOC_SENSOR,
    CONF_BATTERY_CAPACITY,
    CONF_MAX_CHARGE_POWER,
    CONF_CHARGE_EFFICIENCY,
    CONF_MIN_RESERVE,
)

_LOGGER = logging.getLogger(__name__)


class GWSmartCoordinator(DataUpdateCoordinator):
    """Coordinator that reads forecast, price and load sensors and produces a charging schedule."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="gw_smart_charging_coordinator",
            update_interval=timedelta(minutes=5),
        )
        self.entry = entry
        self.config: dict[str, Any] = entry.data or {}
        # cache to accumulate cumulative daily deltas while running
        self._last_daily_cumulative: Optional[float] = None
        self._last_daily_date: Optional[date] = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and normalize forecast, price and load data and compute schedule."""
        try:
            forecast_sensor = self.config.get(CONF_FORECAST_SENSOR)
            price_sensor = self.config.get(CONF_PRICE_SENSOR)
            load_sensor = self.config.get(CONF_LOAD_SENSOR)

            forecast_hourly: List[float] = [0.0] * 24
            price_hourly: List[float] = [0.0] * 24
            load_hourly: List[float] = [0.0] * 24

            forecast_meta = {}
            forecast_timestamps: List[str] = []

            # Parse forecast
            if forecast_sensor:
                state = self.hass.states.get(forecast_sensor)
                if state:
                    _LOGGER.debug("Parsing forecast from %s (state=%s)", forecast_sensor, state.state)
                    forecast_hourly = self._parse_forecast_sensor(state)
                    # build timestamps for the target day and confidence metadata
                    forecast_timestamps = self._build_forecast_timestamps(forecast_sensor, state, forecast_hourly)
                    conf_score, conf_reason, source, slots = self._compute_forecast_confidence(state, forecast_hourly)
                    forecast_meta = {
                        "forecast_confidence": {"score": conf_score, "reason": conf_reason},
                        "forecast_source": source,
                        "forecast_slots_count": slots,
                    }
                    _LOGGER.debug("Forecast meta: %s", forecast_meta)
                else:
                    _LOGGER.debug("Forecast sensor %s not found", forecast_sensor)

            # Parse price
            if price_sensor:
                state = self.hass.states.get(price_sensor)
                if state:
                    _LOGGER.debug("Parsing prices from %s (state=%s)", price_sensor, state.state)
                    price_hourly = self._parse_price_sensor(state)
                else:
                    _LOGGER.debug("Price sensor %s not found", price_sensor)

            # Parse load (supports hourly sensors, mapping, or daily cumulative that resets at midnight)
            if load_sensor:
                state = self.hass.states.get(load_sensor)
                if state:
                    _LOGGER.debug("Parsing load from %s (state=%s)", load_sensor, state.state)
                    load_hourly = self._parse_load_sensor(state, load_sensor)
                    _LOGGER.debug("Aggregated hourly load: %s", load_hourly)
                else:
                    _LOGGER.debug("Load sensor %s not found", load_sensor)

            # Compute schedule (incorporates load)
            schedule = self._compute_schedule(forecast_hourly, price_hourly, load_hourly)

            return {
                "status": "ok",
                "forecast_hourly": forecast_hourly,
                "price_hourly": price_hourly,
                "load_hourly": load_hourly,
                "schedule": schedule,
                "timestamps": forecast_timestamps,
                **forecast_meta,
                "last_update": datetime.utcnow().isoformat(),
            }
        except Exception as err:
            raise UpdateFailed(err) from err

    # ---------- NEW: timestamps builder ----------
    def _build_forecast_timestamps(self, forecast_entity_id: Optional[str], state, forecast_hourly: List[float]) -> List[str]:
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
    def _compute_forecast_confidence(self, state, forecast_hourly: List[float]) -> Tuple[float, str, str, int]:
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
