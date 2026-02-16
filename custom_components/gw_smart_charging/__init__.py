"""Smart Battery Charging Controller v3.0.1 - Home Assistant Integration.

Intelligent battery charging optimization based on electricity spot prices with peak prediction.

Author: Martin Rak
GitHub: https://github.com/someone11221/gw_smart_energy_charging
"""
import logging

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers import config_validation as cv

from .const import DOMAIN, VERSION
from .coordinator import SmartChargingCoordinator
from .views import async_setup_views

_LOGGER = logging.getLogger(__name__)

PLATFORMS = ["sensor", "switch"]

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


async def async_setup(hass: HomeAssistant, config: dict):
    """Set up Smart Battery Charging component."""
    _LOGGER.info(f"Setting up Smart Battery Charging Controller v{VERSION}")
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Smart Battery Charging from a config entry."""
    _LOGGER.info(f"Setting up Smart Battery Charging entry: {entry.title}")
    
    # Create coordinator
    coordinator = SmartChargingCoordinator(hass, entry.data)
    
    # Store coordinator
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = coordinator
    
    # Initial data fetch
    await coordinator.async_config_entry_first_refresh()
    
    # Setup platforms
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    
    # Register services
    await _async_setup_services(hass, coordinator)
    
    # Register dashboard views
    await async_setup_views(hass)
    
    _LOGGER.info("Smart Battery Charging setup complete")
    
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    _LOGGER.info(f"Unloading Smart Battery Charging entry: {entry.title}")
    
    # Unload platforms
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id)
    
    return unload_ok


async def _async_setup_services(hass: HomeAssistant, coordinator: SmartChargingCoordinator):
    """Register services."""
    
    async def handle_force_plan_update(call):
        """Handle force plan update service call."""
        _LOGGER.info("Force plan update service called")
        await coordinator.force_plan_update()
    
    async def handle_get_schedule(call):
        """Handle get charging schedule service call."""
        _LOGGER.debug("Get charging schedule service called")
        
        plan = coordinator.current_plan
        if not plan:
            return {"error": "No charging plan available"}
        
        # Format response
        slots = []
        for slot in plan.slots:
            slots.append({
                "start_time": slot.start_time.isoformat(),
                "end_time": slot.end_time.isoformat(),
                "target_soc": slot.target_soc,
                "price": slot.price,
                "reason": slot.reason,
                "priority": slot.priority,
            })
        
        peaks = []
        for peak in plan.predicted_peaks:
            peaks.append({
                "timestamp": peak.timestamp.isoformat(),
                "price": peak.price,
            })
        
        return {
            "slots": slots,
            "predicted_peaks": peaks,
            "total_cost": plan.total_cost,
            "total_kwh": plan.total_kwh,
            "confidence": plan.confidence,
            "created_at": plan.created_at.isoformat(),
        }
    
    # Register services
    hass.services.async_register(
        DOMAIN,
        "force_plan_update",
        handle_force_plan_update,
    )
    
    hass.services.async_register(
        DOMAIN,
        "get_charging_schedule",
        handle_get_schedule,
    )
    
    _LOGGER.info("Services registered: force_plan_update, get_charging_schedule")
