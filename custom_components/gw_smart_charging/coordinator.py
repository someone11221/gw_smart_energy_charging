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
)

_LOGGER = logging.getLogger(__name__)


class GWSmartCoordinator(DataUpdateCoordinator):
    """Coordinator that reads forecast and price sensors and normalizes data."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="gw_smart_charging_coordinator",
            update_interval=timedelta(minutes=5),
        )
        self.entry = entry
        # store config in data for sensors/services to use
        # expected keys: CONF_FORECAST_SENSOR, CONF_PRICE_SENSOR, ...
        self.config: dict[str, Any] = entry.data or {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and normalize forecast and price data from configured sensors."""
        try:
            forecast_sensor = self.config.get(CONF_FORECAST_SENSOR)
            price_sensor = self.config.get(CONF_PRICE_SENSOR)

            forecast_hourly = [0.0] * 24
            price_hourly = [0.0] * 24

            # Parse forecast
            if forecast_sensor:
                try:
                    state = self.hass.states.get(forecast_sensor)
                    if state is None:
                        _LOGGER.debug("Forecast sensor %s not found", forecast_sensor)
                    else:
                        _LOGGER.debug("Parsing forecast from %s (state=%s)", forecast_sensor, state.state)
                        forecast_hourly = self._parse_forecast_sensor(state)
                        _LOGGER.debug("Aggregated hourly forecast: %s", forecast_hourly)
                except Exception as e:
                    _LOGGER.exception("Error reading forecast sensor %s: %s", forecast_sensor, e)

            # Parse price
            if price_sensor:
                try:
                    state = self.hass.states.get(price_sensor)
                    if state is None:
                        _LOGGER.debug("Price sensor %s not found", price_sensor)
                    else:
                        _LOGGER.debug("Parsing prices from %s (state=%s)", price_sensor, state.state)
                        price_hourly = self._parse_price_sensor(state)
                        _LOGGER.debug("Aggregated hourly prices: %s", price_hourly)
                except Exception as e:
                    _LOGGER.exception("Error reading price sensor %s: %s", price_sensor, e)

            return {
                "status": "ok",
                "forecast_hourly": forecast_hourly,
                "price_hourly": price_hourly,
                "last_update": datetime.utcnow().isoformat(),
            }
        except Exception as err:
            raise UpdateFailed(err) from err

    def _parse_forecast_sensor(self, state) -> List[float]:
        """Normalize forecast sensor to 24 hourly kW values.

        Handles:
        - attribute 'watts' : mapping timestamp -> W (15min slots)
        - attribute 'forecast' / 'values' : list of dicts with 'period_end'/'pv_estimate' or list of numbers
        - state as scalar total kWh (distribute evenly)
        - state_attr lists of length 24 (assumed kW)
        """
        attrs = state.attributes or {}
        # 1) 15min mapping 'watts' (timestamp -> W)
        watts = attrs.get("watts")
        if isinstance(watts, dict) and watts:
            return self._aggregate_timeseries_map_to_hourly(watts, value_in_watts=True)

        # 2) attribute 'forecast' as list of dicts
        items = attrs.get("forecast") or attrs.get("values") or attrs.get("data")
        if isinstance(items, list) and items:
            # If list of numbers and length 24 -> assume already hourly kW
            if all(isinstance(x, (int, float)) for x in items) and len(items) == 24:
                return [round(float(x), 3) for x in items]
            # If list of dicts with period_end and pv_estimate
            result_hour = [0.0] * 24
            cnt = [0] * 24
            for it in items:
                if isinstance(it, dict):
                    pe = it.get("period_end") or it.get("datetime") or it.get("time")
                    val = it.get("pv_estimate") or it.get("pv_estimate_kw") or it.get("value") or it.get("pv_estimate_w")
                    if val is None:
                        continue
                    # If val looks like W (large number) and key says pv_estimate_w, convert later
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
                        # detect if value is in watts vs kW: if attribute name pv_estimate_w or v > 1000, treat as W
                        if "w" in (it.get("pv_estimate_w") or "") or ("pv_estimate_w" in it):
                            v = v / 1000.0
                        elif v > 1000:
                            # heuristic: large numbers likely W -> convert
                            v = v / 1000.0
                        result_hour[hour] += v
                        cnt[hour] += 1
                    except Exception:
                        continue
            # average where counts >0
            out = []
            for h in range(24):
                if cnt[h] > 0:
                    out.append(round(result_hour[h] / cnt[h], 3))
                else:
                    out.append(0.0)
            return out

        # 3) attribute that is already hourly list: look for keys like 'hourly'
        hourly = attrs.get("hourly") or attrs.get("hourly_kwh") or attrs.get("hourly_kw")
        if isinstance(hourly, list) and len(hourly) == 24:
            # if values are energy kWh/h they're equal numerically to kW, so use as-is
            return [round(float(x), 3) for x in hourly]

        # 4) state is a scalar total kWh (distribute evenly)
        try:
            total = float(state.state)
            # if total looks like very large maybe it's watts — ignore heuristic here
            per_hour = total / 24.0
            return [round(per_hour, 3) for _ in range(24)]
        except Exception:
            _LOGGER.debug("Unable to parse forecast sensor %s attributes %s", state.entity_id, list(attrs.keys()))
            return [0.0] * 24

    def _parse_price_sensor(self, state) -> List[float]:
        """Normalize price sensor to 24 hourly currency/kWh values.

        Handles:
        - attributes 'tomorrow_hourly_prices' or 'today_hourly_prices' (lists of 24 floats)
        - mapping timestamp->price
        - attribute 'forecast' list of dicts with period_end and price/value
        - tries to convert units like /MWh -> /kWh by dividing by 1000 if unit indicates so
        """
        attrs = state.attributes or {}

        # 1) direct tomorrow or today lists
        tomorrow = attrs.get("tomorrow_hourly_prices")
        if isinstance(tomorrow, list) and len(tomorrow) >= 24:
            # take first 24
            try:
                return [round(float(x), 4) for x in tomorrow[:24]]
            except Exception:
                pass

        today = attrs.get("today_hourly_prices")
        if isinstance(today, list) and len(today) >= 24:
            try:
                return [round(float(x), 4) for x in today[:24]]
            except Exception:
                pass

        # 2) mapping timestamp -> price
        for keyname in ("prices", "values", "prices_map", "price_map"):
            mapping = attrs.get(keyname)
            if isinstance(mapping, dict) and mapping:
                return self._aggregate_timeseries_map_to_hourly(mapping, value_in_watts=False, unit=state.attributes.get("unit_of_measurement", ""))

        # 3) forecast list of dicts
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

    def _aggregate_timeseries_map_to_hourly(self, mapping: Dict[str, Any], value_in_watts: bool = False, unit: str = "") -> List[float]:
        """Aggregate a mapping timestamp->value (e.g. 15min slots) into 24 hourly values.

        If value_in_watts=True, convert values (W) -> kW by dividing by 1000.
        For prices, unit may indicate /MWh and will be converted to /kWh by dividing by 1000 when detected.
        """
        sums = [0.0] * 24
        counts = [0] * 24
        for k, v in mapping.items():
            try:
                # k expected ISO timestamp string
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
                    # price conversion heuristic: if unit says MWh convert to /kWh
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
