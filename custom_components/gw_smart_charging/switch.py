"""Switch platform for GW Smart Charging - controls battery charging from grid."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, DEFAULT_NAME, CONF_CHARGING_ON_SCRIPT, CONF_CHARGING_OFF_SCRIPT, CONF_ENABLE_AUTOMATION
from .coordinator import GWSmartCoordinator

_LOGGER = logging.getLogger(__name__)


def get_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return device info for the integration."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=DEFAULT_NAME,
        manufacturer="GW Energy Solutions",
        model="Smart Battery Charging Controller",
        sw_version="1.9.0",
        configuration_url="https://github.com/someone11221/gw_smart_energy_charging",
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up switch for the config entry."""
    coordinator: GWSmartCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        GWSmartChargingSwitch(coordinator, entry),
    ]

    async_add_entities(entities, True)


class GWSmartChargingSwitch(CoordinatorEntity, SwitchEntity):
    """Switch that controls battery charging based on optimized schedule."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        """Initialize the switch."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} Auto Charging"
        self._attr_unique_id = f"{entry.entry_id}_auto_charging"
        self._attr_icon = "mdi:battery-charging"
        self._is_on = False
        self._update_from_coordinator()

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        self._update_from_coordinator()
        super()._handle_coordinator_update()

    def _update_from_coordinator(self) -> None:
        """Update switch state based on coordinator data and schedule."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule") or []
        
        if not schedule:
            self._is_on = False
            return
        
        # Get current 15-min slot
        from datetime import datetime
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        
        if 0 <= slot < len(schedule):
            current_slot = schedule[slot]
            # Should charge if schedule says so
            self._is_on = current_slot.get("should_charge", False)
        else:
            self._is_on = False

    @property
    def is_on(self) -> bool:
        """Return true if switch is on (charging enabled)."""
        return self._is_on

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional state attributes."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule") or []
        
        from datetime import datetime
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        current_slot = schedule[slot] if 0 <= slot < len(schedule) else {}
        
        # Count charging periods
        charging_slots = sum(1 for s in schedule if s.get("should_charge", False))
        
        return {
            "current_mode": current_slot.get("mode", "unknown"),
            "current_price": current_slot.get("price_czk_kwh", 0.0),
            "current_soc": current_slot.get("soc_pct_end", 0.0),
            "charging_slots_today": charging_slots,
            "automation_enabled": self.coordinator.config.get(CONF_ENABLE_AUTOMATION, True),
            "charging_on_script": self.coordinator.config.get(CONF_CHARGING_ON_SCRIPT, ""),
            "charging_off_script": self.coordinator.config.get(CONF_CHARGING_OFF_SCRIPT, ""),
        }

    async def async_turn_on(self, **kwargs: Any) -> None:
        """Turn the switch on (enable charging)."""
        # This would trigger the charging script if automation is enabled
        _LOGGER.info("Auto charging switch turned ON")
        self._is_on = True
        self.async_write_ha_state()
        
        # If automation enabled, call the charging ON script
        if self.coordinator.config.get(CONF_ENABLE_AUTOMATION, True):
            charging_on_script = self.coordinator.config.get(CONF_CHARGING_ON_SCRIPT)
            if charging_on_script:
                await self.hass.services.async_call(
                    "script", "turn_on", {"entity_id": charging_on_script}, blocking=True
                )

    async def async_turn_off(self, **kwargs: Any) -> None:
        """Turn the switch off (disable charging)."""
        _LOGGER.info("Auto charging switch turned OFF")
        self._is_on = False
        self.async_write_ha_state()
        
        # If automation enabled, call the charging OFF script
        if self.coordinator.config.get(CONF_ENABLE_AUTOMATION, True):
            charging_off_script = self.coordinator.config.get(CONF_CHARGING_OFF_SCRIPT)
            if charging_off_script:
                await self.hass.services.async_call(
                    "script", "turn_on", {"entity_id": charging_off_script}, blocking=True
                )
