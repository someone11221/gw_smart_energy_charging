"""Switch platform for Smart Battery Charging Controller."""
import logging

from homeassistant.components.switch import SwitchEntity
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity

from .const import DOMAIN, VERSION
from .coordinator import SmartChargingCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up Smart Battery Charging switches."""
    coordinator: SmartChargingCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    switches = [
        AutoChargingSwitch(coordinator, entry),
    ]
    
    async_add_entities(switches)
    _LOGGER.info(f"Added {len(switches)} switches")


class SmartChargingBaseSwitch(CoordinatorEntity, SwitchEntity):
    """Base switch for Smart Battery Charging."""
    
    def __init__(self, coordinator: SmartChargingCoordinator, entry: ConfigEntry):
        """Initialize switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_has_entity_name = True
    
    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Smart Battery Charging Controller",
            "manufacturer": "Martin Rak",
            "model": f"Intelligent Charging v{VERSION}",
            "sw_version": VERSION,
        }


class AutoChargingSwitch(SmartChargingBaseSwitch):
    """Switch to enable/disable automatic charging."""
    
    _attr_name = "Auto Charging"
    _attr_icon = "mdi:power"
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self._entry.entry_id}_auto_charging"
    
    @property
    def is_on(self):
        """Return true if auto charging is enabled."""
        return self.coordinator._auto_charging_enabled
    
    async def async_turn_on(self, **kwargs):
        """Turn on auto charging."""
        await self.coordinator.set_auto_charging(True)
        await self.coordinator.async_request_refresh()
        _LOGGER.info("Auto charging enabled via switch")
    
    async def async_turn_off(self, **kwargs):
        """Turn off auto charging."""
        await self.coordinator.set_auto_charging(False)
        await self.coordinator.async_request_refresh()
        _LOGGER.info("Auto charging disabled via switch")
    
    @property
    def extra_state_attributes(self):
        """Return switch attributes."""
        attrs = {
            "enabled": self.coordinator._auto_charging_enabled,
            "charging_active": self.coordinator._charging_active,
        }
        
        if self.coordinator.current_plan:
            attrs["planned_slots"] = len(self.coordinator.current_plan.slots)
            attrs["predicted_peaks"] = len(self.coordinator.current_plan.predicted_peaks)
        
        return attrs
