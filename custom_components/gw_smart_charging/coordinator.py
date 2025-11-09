from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional
from datetime import timedelta, datetime

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_FORECAST_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_SOC_SENSOR,
    CONF_BATTERY_CAPACITY,
    CONF_MAX_CHARGE_POWER,
    CONF_CHARGE_EFFICIENCY,
    CONF_MIN_RESERVE,
)

_LOGGER = logging.getLogger(__name__)


class GWSmartCoordinator(DataUpdateCoordinator):
    """Coordinator that reads forecast and price sensors and produces a charging schedule."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="gw_smart_charging_coordinator",
            update_interval=timedelta(minutes=5),
        )
        self.entry = entry
        self.config: dict[str, Any] = entry.data or {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and normalize forecast and price data and compute schedule."""
        try:
            forecast_sensor = self.config.get(CONF_FORECAST_SENSOR)
            price_sensor = self.config.get(CONF_PRICE_SENSOR)

            forecast_hourly: List[float] = [0.0] * 24
            price_hourly: List[float] = [0.0] * 24

            # Parse forecast
            if forecast_sensor:
                state = self.hass.states.get(forecast_sensor)
                if state:
                    _LOGGER.debug("Parsing forecast from %s (state=%s)", forecast_sensor, state.state)
                    forecast_hourly = self._parse_forecast_sensor(state)
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

            # Compute schedule
            schedule = self._compute_schedule(forecast_hourly, price_hourly)

            return {
                "status": "ok",
                "forecast_hourly": forecast_hourly,
                "price_hourly": price_hourly,
                "schedule": schedule,
                "last_update": datetime.utcnow().isoformat(),
            }
        except Exception as err:
            raise UpdateFailed(err) from err

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
                val = it.get("price") or it.get("value")
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

        _LOGGER.debug("Unable to parse price sensor %s attributes %s unit=%s", state.entity_id, list(attrs.keys()), state.attributes.get("unit_of_measurement"))
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
                out.append(round(sums[h] / counts[h], 4 if not value_in_watts else 3))
            else:
                out.append(0.0)
        return out

    def _compute_schedule(self, forecast: List[float], prices: List[float]) -> List[Dict[str, Any]]:
        """Compute a simple hourly plan.

        Returns list[24] with dicts:
        { hour, mode, pv_power_kW, price, planned_power_kW, soc_kwh_end, soc_pct_end }

        Strategy:
        - Prioritize PV when available (use PV up to max_charge_power).
        - When PV absent, charge from grid during cheap hours (<= 25th percentile) if battery not full.
        - Otherwise, if SOC > min_reserve -> mark as 'battery' (implying discharge use).
        - Else 'idle'.
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
                    # if value looks like percent (0-100) convert to fraction
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

            mode = "idle"
            planned_power = 0.0  # positive = charge into battery (kW), negative = discharge (kW)
            # If PV available - charge from PV (cap at max_charge)
            if pv > 0.05:  # small threshold
                charge_power = min(pv, max_charge)
                # limit to capacity remaining
                capacity_left_kwh = capacity - soc_kwh
                max_possible_charge = capacity_left_kwh  # over 1 hour
                charge_power = min(charge_power, max_possible_charge)
                # apply efficiency: energy stored = charge_power * eff * 1h
                stored_kwh = charge_power * eff
                soc_kwh += stored_kwh
                planned_power = charge_power
                mode = "pv"
            else:
                # no PV; consider grid charging if cheap and space in battery
                capacity_left_kwh = capacity - soc_kwh
                if price_threshold > 0 and price > 0 and price <= price_threshold and capacity_left_kwh > 0.01:
                    charge_power = min(max_charge, capacity_left_kwh)
                    stored_kwh = charge_power * eff
                    soc_kwh += stored_kwh
                    planned_power = charge_power
                    mode = "grid"
                else:
                    # consider using battery if above reserve
                    if soc_kwh > min_reserve_kwh + 0.1:
                        # plan to discharge (represent as negative planned_power)
                        discharge_power = min(max_charge, soc_kwh - min_reserve_kwh)
                        # withdraw energy for 1h
                        soc_kwh -= discharge_power / eff  # account for inefficiency on discharge
                        planned_power = -discharge_power
                        mode = "battery"
                    else:
                        mode = "idle"
                        planned_power = 0.0

            # clamp soc_kwh between 0 and capacity
            soc_kwh = max(0.0, min(capacity, soc_kwh))
            soc_pct = round((soc_kwh / capacity) * 100.0, 2)

            schedule.append({
                "hour": h,
                "mode": mode,
                "pv_power_kW": round(pv, 3),
                "price_czk_kwh": round(price, 4),
                "planned_power_kW": round(planned_power, 3),
                "soc_kwh_end": round(soc_kwh, 3),
                "soc_pct_end": soc_pct,
            })

        return schedule
