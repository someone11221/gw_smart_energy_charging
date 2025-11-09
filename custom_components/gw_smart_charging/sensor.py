from __future__ import annotations
from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DEFAULT_NAME, ATTR_FORECAST

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities):
    coordinator = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([ForecastNextDaySensor(coordinator, entry)], True)

class ForecastNextDaySensor(CoordinatorEntity, SensorEntity):
    def __init__(self, coordinator, entry):
        super().__init__(coordinator)
        self.coordinator = coordinator
        self.entry = entry
        self._attr_name = entry.data.get("name", DEFAULT_NAME)
        self._attr_unique_id = f"gw_smart_charging_{entry.entry_id}"

    @property
    def native_value(self):
        schedule = self.coordinator.schedule or {}
        grid_hours = sum(1 for v in schedule.values() if v.get("mode") == "grid")
        pv_hours = sum(1 for v in schedule.values() if v.get("mode") == "pv")
        return f"grid:{grid_hours} pv:{pv_hours}"

    @property
    def extra_state_attributes(self):
        data = self.coordinator.data or {}
        return {
            ATTR_FORECAST: data.get("schedule", self.coordinator.schedule),
            "prices": data.get("prices"),
            "forecast_series": data.get("forecast"),
            "last_update": data.get("timestamp"),
            "current_soc": data.get("current_soc"),
            "goodwe_switch": data.get("goodwe_switch"),
        }

    async def async_update(self):
        await self.coordinator.async_request_refresh()
