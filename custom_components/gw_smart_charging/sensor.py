from __future__ import annotations

from typing import Any, List
from datetime import datetime

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
