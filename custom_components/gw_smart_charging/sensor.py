from __future__ import annotations

import logging
from typing import Any, List, Optional
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import GWSmartCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up sensors for the config entry."""
    coordinator: GWSmartCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        GWSmartStatusSensor(coordinator, entry.entry_id),
        GWSmartForecastSensor(coordinator, entry.entry_id),
        GWSmartPriceSensor(coordinator, entry.entry_id),
        # series sensors for Lovelace plotting (names match existing ones in your instance)
        GWSmartSeriesSensor(coordinator, entry.entry_id, "pv"),
        GWSmartSeriesSensor(coordinator, entry.entry_id, "load"),
        GWSmartSeriesSensor(coordinator, entry.entry_id, "battery_charge"),
        GWSmartSeriesSensor(coordinator, entry.entry_id, "battery_discharge"),
        GWSmartSeriesSensor(coordinator, entry.entry_id, "grid_import"),
    ]

    async_add_entities(entities, True)


class GWSmartStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor reporting integration status."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Forecast Status"
        self._attr_unique_id = f"{entry_id}_status"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        return data.get("status", "unknown")


class GWSmartForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing hourly PV forecast (kW) plus planned schedule and timestamps."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Forecast"
        self._attr_unique_id = f"{entry_id}_forecast"

    @property
    def native_value(self) -> float:
        """Return a simple numeric state (peak kW) for quick overview."""
        data = self.coordinator.data or {}
        hourly: List[float] = data.get("forecast_hourly") or []
        if not hourly:
            return 0.0
        return round(max(hourly), 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        hourly: List[float] = data.get("forecast_hourly") or [0.0] * 24
        schedule: List[dict] = data.get("schedule") or []
        plan_hourly = [s.get("mode", "idle") for s in schedule] if schedule else []
        plan_power = [s.get("planned_power_kW", 0.0) for s in schedule] if schedule else []
        timestamps = data.get("timestamps") or []
        # forecast confidence and metadata (may be added by coordinator)
        forecast_conf = data.get("forecast_confidence") or {}
        forecast_source = data.get("forecast_source", "")
        forecast_slots = data.get("forecast_slots_count", 0)
        return {
            "hourly": hourly,
            "timestamps": timestamps,
            "schedule": schedule,
            "plan_hourly": plan_hourly,
            "plan_power_kW": plan_power,
            "forecast_confidence": forecast_conf,
            "forecast_source": forecast_source,
            "forecast_slots_count": forecast_slots,
        }


class GWSmartPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing hourly prices. State = current hour price, attribute 'hourly' = list[24]."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Price"
        self._attr_unique_id = f"{entry_id}_price"
        self._attr_unit_of_measurement = "CZK/kWh"

    @property
    def native_value(self) -> float:
        """Return current hour price (CZK/kWh) if available."""
        data = self.coordinator.data or {}
        hourly: List[float] = data.get("price_hourly") or []
        timestamps: List[str] = data.get("timestamps") or []
        arr = hourly
        if not arr:
            return 0.0
        # pick value closest to now using timestamps if provided, else use current hour
        try:
            if timestamps and len(timestamps) >= len(arr):
                now_ms = int(datetime.now().timestamp() * 1000)
                # find index of timestamp closest to now
                diffs = []
                for t in timestamps[: len(arr)]:
                    try:
                        t_ms = int(datetime.fromisoformat(t).timestamp() * 1000)
                    except Exception:
                        # fallback: parse "HH:MM"
                        if isinstance(t, str) and t.count(":") == 1:
                            hh = int(t.split(":")[0])
                            dt = datetime.now().replace(hour=hh, minute=0, second=0, microsecond=0)
                            t_ms = int(dt.timestamp() * 1000)
                        else:
                            t_ms = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
                    diffs.append(abs(now_ms - t_ms))
                idx = diffs.index(min(diffs))
                return round(float(arr[idx]), 4)
            else:
                hour = datetime.now().hour
                return round(float(arr[hour]), 4)
        except Exception:
            return round(float(arr[0]), 4)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        hourly: List[float] = data.get("price_hourly") or [0.0] * 24
        timestamps: List[str] = data.get("timestamps") or []
        return {"hourly": hourly, "timestamps": timestamps}


class GWSmartSeriesSensor(CoordinatorEntity, SensorEntity):
    """Generic series sensor for Lovelace plotting.

    series_type in {"pv","load","battery_charge","battery_discharge","grid_import"}
    Exposes attributes:
      - hourly: list[24] of floats (kW)
      - timestamps: list[24] of ISO hour labels (strings)
    State is current hour value (float) chosen by nearest timestamp.
    """

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str, series_type: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self.series_type = series_type
        # Names and unique_ids include "forecast" part so they match existing entity ids in your system
        self._attr_name = f"{DEFAULT_NAME} Series {series_type}"
        self._attr_unique_id = f"{entry_id}_series_{series_type}"
        self._attr_unit_of_measurement = "kW"

    def _build_series_from_schedule(self, schedule: List[dict]) -> List[float]:
        # Derive series from schedule data
        pv = []
        load = []
        planned = []
        net_pv = []
        for s in schedule:
            pv_val = float(s.get("pv_power_kW", 0.0))
            load_val = float(s.get("load_kW", 0.0))
            planned_val = float(s.get("planned_power_kW", 0.0))  # positive = charge, negative = discharge
            net = pv_val - load_val
            pv.append(round(pv_val, 3))
            load.append(round(load_val, 3))
            planned.append(round(planned_val, 3))
            net_pv.append(round(net, 3))

        battery_charge = [p if p > 0 else 0.0 for p in planned]
        battery_discharge = [-p if p < 0 else 0.0 for p in planned]

        grid_import = []
        for i in range(len(pv)):
            gi = max(0.0, load[i] - pv[i])
            # battery discharge reduces import; battery charge from grid increases import
            if battery_discharge[i] > 0:
                gi = max(0.0, gi - battery_discharge[i])
            if battery_charge[i] > 0:
                surplus = max(0.0, pv[i] - load[i])
                extra_charge_from_grid = max(0.0, battery_charge[i] - surplus)
                gi += extra_charge_from_grid
            grid_import.append(round(gi, 3))

        mapping = {
            "pv": pv,
            "load": load,
            "battery_charge": battery_charge,
            "battery_discharge": battery_discharge,
            "grid_import": grid_import,
            "net_pv": net_pv,
        }
        return mapping.get(self.series_type, [0.0] * 24)

    def _build_series_from_fallback(self, coordinator_data: dict) -> List[float]:
        # fallback: use forecast_hourly and load_hourly if schedule absent
        forecast = coordinator_data.get("forecast_hourly") or [0.0] * 24
        load = coordinator_data.get("load_hourly") or [0.0] * 24
        net_pv = [round(forecast[i] - load[i], 3) for i in range(24)]
        battery_charge = [0.0] * 24
        battery_discharge = [0.0] * 24
        grid_import = [max(0.0, load[i] - forecast[i]) for i in range(24)]
        mapping = {
            "pv": forecast,
            "load": load,
            "battery_charge": battery_charge,
            "battery_discharge": battery_discharge,
            "grid_import": grid_import,
            "net_pv": net_pv,
        }
        return mapping.get(self.series_type, [0.0] * 24)

    def _build_timestamps(self, coordinator_data: dict) -> List[str]:
        # Prefer coordinator timestamps if provided; otherwise build simple "HH:MM" labels
        timestamps = coordinator_data.get("timestamps")
        if isinstance(timestamps, list) and len(timestamps) >= 24:
            return timestamps[:24]
        labels = []
        for h in range(24):
            labels.append(f"{h:02d}:00")
        return labels

    def _value_for_nearest_timestamp(self, arr: List[float], timestamps: List[str]) -> float:
        """Return value from arr at index nearest to now using provided ISO timestamps if possible."""
        if not arr:
            return 0.0
        try:
            if timestamps and len(timestamps) >= len(arr):
                now_ms = int(datetime.now().timestamp() * 1000)
                diffs = []
                for t in timestamps[: len(arr)]:
                    try:
                        t_ms = int(datetime.fromisoformat(t).timestamp() * 1000)
                    except Exception:
                        if isinstance(t, str) and t.count(":") == 1:
                            hh = int(t.split(":")[0])
                            dt = datetime.now().replace(hour=hh, minute=0, second=0, microsecond=0)
                            t_ms = int(dt.timestamp() * 1000)
                        else:
                            t_ms = int(datetime.now().replace(hour=0, minute=0, second=0, microsecond=0).timestamp() * 1000)
                    diffs.append(abs(now_ms - t_ms))
                idx = diffs.index(min(diffs))
                return round(float(arr[idx]), 3)
            else:
                idx = datetime.now().hour
                return round(float(arr[idx]), 3)
        except Exception:
            return round(float(arr[0]), 3)

    @property
    def native_value(self) -> float:
        data = self.coordinator.data or {}
        schedule = data.get("schedule")
        if schedule:
            arr = self._build_series_from_schedule(schedule)
        else:
            arr = self._build_series_from_fallback(data)
        timestamps = data.get("timestamps") or []
        return self._value_for_nearest_timestamp(arr, timestamps)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        schedule = data.get("schedule")
        if schedule:
            arr = self._build_series_from_schedule(schedule)
        else:
            arr = self._build_series_from_fallback(data)
        timestamps = self._build_timestamps(data)
        return {"hourly": arr, "timestamps": timestamps}
