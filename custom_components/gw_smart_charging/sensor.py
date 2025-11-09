from __future__ import annotations

from typing import Any, List
from datetime import datetime, timedelta

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import GWSmartCoordinator


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up sensors for the config entry."""
    coordinator: GWSmartCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        GWSmartStatusSensor(coordinator, entry.entry_id),
        GWSmartForecastSensor(coordinator, entry.entry_id),
        GWSmartPriceSensor(coordinator, entry.entry_id),
        # series sensors for Lovelace plotting
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
        self._attr_name = f"{DEFAULT_NAME} Status"
        self._attr_unique_id = f"{entry_id}_status"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        return data.get("status", "unknown")


class GWSmartForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing hourly PV forecast (kW) plus planned schedule."""

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
        return {
            "hourly": hourly,
            "schedule": schedule,
            "plan_hourly": plan_hourly,
            "plan_power_kW": plan_power,
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
        if not hourly:
            return 0.0
        try:
            hour = datetime.now().hour
            return round(float(hourly[hour]), 4)
        except Exception:
            return round(float(hourly[0]), 4)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        hourly: List[float] = data.get("price_hourly") or [0.0] * 24
        return {"hourly": hourly}


class GWSmartSeriesSensor(CoordinatorEntity, SensorEntity):
    """Generic series sensor for Lovelace plotting.

    series_type in {"pv","load","battery_charge","battery_discharge","grid_import"}
    Exposes attributes:
      - hourly: list[24] of floats (kW)
      - timestamps: list[24] of ISO hour labels (strings)
    State is current hour value (float).
    """

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str, series_type: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self.series_type = series_type
        self._attr_name = f"{DEFAULT_NAME} Series {series_type}"
        self._attr_unique_id = f"{entry_id}_series_{series_type}"
        self._attr_unit_of_measurement = "kW"

    def _build_series_from_schedule(self, schedule: List[dict]) -> List[float]:
        # If schedule available, derive series directly
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

        # battery_charge: planned positive values
        battery_charge = [p if p > 0 else 0.0 for p in planned]
        battery_discharge = [-p if p < 0 else 0.0 for p in planned]

        # grid import: compute approximate grid import after battery action
        grid_import = []
        for i in range(len(pv)):
            # initial grid import before battery: max(0, load - pv)
            gi = max(0.0, load[i] - pv[i])
            # battery discharge reduces import; battery charge from grid increases import
            if battery_discharge[i] > 0:
                gi = max(0.0, gi - battery_discharge[i])
            if battery_charge[i] > 0:
                # if charge came from grid (mode 'grid') we cannot be 100% sure; use planned_charge beyond surplus as grid import
                # best-effort: if planned charge > max(0, net_pv) assume extra from grid
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
        planned = [0.0] * 24
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

    def _build_timestamps(self) -> List[str]:
        # give hour labels for next 24 slots; align with schedule index (0..23)
        now = datetime.now()
        # prefer showing hours 0..23 of the schedule/day (no timezone conversion here)
        labels = []
        for h in range(24):
            labels.append(f"{h:02d}:00")
        return labels

    @property
    def native_value(self) -> float:
        data = self.coordinator.data or {}
        schedule = data.get("schedule")
        if schedule:
            arr = self._build_series_from_schedule(schedule)
        else:
            arr = self._build_series_from_fallback(data)
        try:
            hour = datetime.now().hour
            return round(float(arr[hour]), 3)
        except Exception:
            return round(float(arr[0]), 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        schedule = data.get("schedule")
        if schedule:
            arr = self._build_series_from_schedule(schedule)
        else:
            arr = self._build_series_from_fallback(data)
        timestamps = self._build_timestamps()
        return {"hourly": arr, "timestamps": timestamps}
