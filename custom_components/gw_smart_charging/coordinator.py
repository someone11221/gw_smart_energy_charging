from __future__ import annotations
from typing import Any, Dict, List
import logging
import json
from datetime import timedelta, datetime

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DEFAULT_SCAN_INTERVAL,
    CONF_FORECAST_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_PV_POWER_SENSOR,
    CONF_GOODWE_SWITCH,
    CONF_SOC_SENSOR,
    CONF_BATTERY_CAPACITY,
    CONF_MAX_CHARGE_POWER,
    CONF_CHARGE_EFFICIENCY,
    CONF_MIN_RESERVE,
    CONF_ENABLE_AUTOMATION,
    CONF_SWITCH_ON_MEANS_CHARGE,
)

_LOGGER = logging.getLogger(__name__)

def _parse_hourly_from_state(state) -> List[float]:
    if state is None:
        return []
    # Try JSON list in state
    try:
        data = json.loads(state.state)
        if isinstance(data, list) and len(data) >= 24:
            return [float(x) for x in data[:24]]
    except Exception:
        pass
    # Try attributes
    for k in ("forecast", "hourly", "hours", "values", "tomorrow", "prices"):
        if state.attributes and k in state.attributes:
            val = state.attributes[k]
            if isinstance(val, list) and len(val) >= 24:
                try:
                    return [float(x) for x in val[:24]]
                except Exception:
                    continue
    # CSV fallback
    if isinstance(state.state, str) and "," in state.state:
        parts = [p.strip() for p in state.state.split(",")]
        if len(parts) >= 24:
            try:
                return [float(x) for x in parts[:24]]
            except Exception:
                pass
    return []

class GWSmartCoordinator(DataUpdateCoordinator):
    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        self.hass = hass
        self.entry = entry
        self.config = entry.data
        super().__init__(hass, _LOGGER, name="gw_smart_charging", update_interval=timedelta(seconds=DEFAULT_SCAN_INTERVAL))
        self.forecast: List[float] = []
        self.prices: List[float] = []
        self.schedule: Dict[int, Dict[str, Any]] = {}

    async def _async_update_data(self) -> Dict[str, Any]:
        try:
            forecast_entity = self.config.get(CONF_FORECAST_SENSOR)
            price_entity = self.config.get(CONF_PRICE_SENSOR)
            pv_entity = self.config.get(CONF_PV_POWER_SENSOR)
            soc_entity = self.config.get(CONF_SOC_SENSOR)
            goodwe_switch = self.config.get(CONF_GOODWE_SWITCH)

            state_fore = self.hass.states.get(forecast_entity) if forecast_entity else None
            state_price = self.hass.states.get(price_entity) if price_entity else None
            state_pv = self.hass.states.get(pv_entity) if pv_entity else None
            state_soc = self.hass.states.get(soc_entity) if soc_entity else None

            forecast = _parse_hourly_from_state(state_fore)
            prices = _parse_hourly_from_state(state_price)

            self.forecast = forecast
            self.prices = prices

            # Read SOC numeric
            current_soc = None
            if state_soc and state_soc.state not in (None, ""):
                try:
                    current_soc = float(state_soc.state)
                except Exception:
                    current_soc = None

            battery_capacity = float(self.config.get(CONF_BATTERY_CAPACITY, 17))
            max_charge_power = float(self.config.get(CONF_MAX_CHARGE_POWER, 3.7))
            efficiency = float(self.config.get(CONF_CHARGE_EFFICIENCY, 0.95))
            min_reserve = float(self.config.get(CONF_MIN_RESERVE, 10)) / 100.0
            enable_automation = bool(self.config.get(CONF_ENABLE_AUTOMATION, False))

            schedule: Dict[int, Dict[str, Any]] = {}

            if len(forecast) >= 24 and len(prices) >= 24 and current_soc is not None:
                required_kwh = max(0.0, battery_capacity * ((100.0 - current_soc) / 100.0))
                # Reserve
                required_kwh = max(0.0, required_kwh - battery_capacity * min_reserve)

                # prepare hour infos
                hours = list(range(24))
                hour_infos = []
                for h in hours:
                    pv_kw = float(forecast[h])
                    price = float(prices[h])
                    hour_infos.append({"hour": h, "pv_kw": pv_kw, "price": price})

                # allocate PV contributions first (we assume PV kW for hour equals kWh potential)
                pv_threshold = 0.1
                pv_hours = [h for h in hour_infos if h["pv_kw"] > pv_threshold]
                pv_energy_est = sum(h["pv_kw"] for h in pv_hours)  # approximate kWh available

                remaining_needed = max(0.0, required_kwh - pv_energy_est)

                # sort remaining hours (non-pv) by price ascending
                non_pv_hours = [h for h in hour_infos if h["pv_kw"] <= pv_threshold]
                non_pv_sorted = sorted(non_pv_hours, key=lambda x: x["price"])

                planned_grid: Dict[int, float] = {}
                for h in non_pv_sorted:
                    if remaining_needed <= 0:
                        break
                    available = max_charge_power * efficiency
                    take = min(available, remaining_needed)
                    planned_grid[h["hour"]] = take
                    remaining_needed -= take

                for h in hour_infos:
                    mode = "idle"
                    planned_kwh = planned_grid.get(h["hour"], 0.0)
                    if h["pv_kw"] > pv_threshold:
                        mode = "pv"
                    if planned_kwh > 0:
                        mode = "grid"
                    schedule[h["hour"]] = {
                        "mode": mode,
                        "pv_kw": round(h["pv_kw"], 3),
                        "price": round(h["price"], 6),
                        "planned_grid_kwh": round(planned_kwh, 3),
                    }
            else:
                now = datetime.utcnow().hour
                schedule[now] = {
                    "mode": "idle",
                    "pv_kw": float(state_pv.state) if state_pv and state_pv.state not in (None, "") else 0.0,
                    "price": float(state_price.state) if state_price and state_price.state not in (None, "") else 0.0,
                    "planned_grid_kwh": 0.0,
                }

            self.schedule = schedule

            result = {
                "forecast": self.forecast,
                "prices": self.prices,
                "schedule": self.schedule,
                "timestamp": datetime.utcnow().isoformat(),
                "goodwe_switch": goodwe_switch,
                "current_soc": current_soc,
            }
            return result
        except Exception as err:
            raise UpdateFailed(err)

    async def apply_current_hour(self) -> None:
        cfg = self.entry.data
        goodwe_switch = cfg.get(CONF_GOODWE_SWITCH)
        switch_on_means_charge = cfg.get(CONF_SWITCH_ON_MEANS_CHARGE, True)
        enable_automation = cfg.get(CONF_ENABLE_AUTOMATION, False)
        if not enable_automation or not goodwe_switch:
            _LOGGER.debug("Automation disabled or no goodwe switch configured")
            return

        now_hour = datetime.utcnow().hour
        hour_info = self.schedule.get(now_hour)
        if not hour_info:
            _LOGGER.debug("No schedule for hour %s", now_hour)
            return

        desired_mode = hour_info.get("mode")
        try:
            if desired_mode == "grid":
                if switch_on_means_charge:
                    await self.hass.services.async_call("switch", "turn_on", {"entity_id": goodwe_switch})
                else:
                    await self.hass.services.async_call("switch", "turn_off", {"entity_id": goodwe_switch})
            else:
                if switch_on_means_charge:
                    await self.hass.services.async_call("switch", "turn_off", {"entity_id": goodwe_switch})
                else:
                    await self.hass.services.async_call("switch", "turn_on", {"entity_id": goodwe_switch})
        except Exception as e:
            _LOGGER.error("Failed to apply schedule to %s: %s", goodwe_switch, e)
