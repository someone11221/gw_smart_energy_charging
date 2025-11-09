from __future__ import annotations

from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DEFAULT_NAME


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    """Set up sensors from a config entry."""
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([GWSmartSensor(coordinator, entry.entry_id)], True)


class GWSmartSensor(CoordinatorEntity, SensorEntity):
    """A very small sensor exposing integration status."""

    def __init__(self, coordinator, entry_id: str):
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = DEFAULT_NAME
        self._attr_unique_id = f"{entry_id}_gw_smart_forecast"

    @property
    def native_value(self) -> Any:
        """Return the state of the sensor."""
        data = self.coordinator.data or {}
        # Expose a simple textual status for now
        return data.get("status", "unknown")
