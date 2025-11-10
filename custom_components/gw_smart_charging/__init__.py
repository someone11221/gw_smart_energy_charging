from __future__ import annotations

import logging
from pathlib import Path

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.components import frontend

from .const import DOMAIN, PLATFORMS

_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config) -> bool:
    """Set up integration (module import)."""
    hass.data.setdefault(DOMAIN, {})
    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up for a config entry."""
    hass.data.setdefault(DOMAIN, {})

    # local imports to avoid startup side-effects
    from .coordinator import GWSmartCoordinator
    from .services import async_setup_services
    from .view import GWSmartChargingDashboardView

    coordinator = GWSmartCoordinator(hass, entry)
    await coordinator.async_config_entry_first_refresh()

    hass.data[DOMAIN][entry.entry_id] = coordinator

    # Register dashboard view
    hass.http.register_view(GWSmartChargingDashboardView(hass))
    
    # Register custom Lovelace card
    await _async_register_lovelace_card(hass)
    
    # Register panel in sidebar
    if DOMAIN not in hass.data.get("frontend_panels", {}):
        await _async_register_panel(hass)

    # Forward setup for platforms (use correct HA API)
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    await async_setup_services(hass)

    async def _async_update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
        """Handle options update."""
        await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(entry.add_update_listener(_async_update_listener))
    _LOGGER.debug("GW Smart Charging setup complete")
    return True


async def _async_register_lovelace_card(hass: HomeAssistant) -> None:
    """Register the custom Lovelace card."""
    # Get the path to the www directory
    integration_dir = Path(__file__).parent
    www_dir = integration_dir / "www"
    
    # Register the resource
    try:
        await hass.http.async_register_static_path(
            f"/gw_smart_charging/gw-smart-charging-card.js",
            str(www_dir / "gw-smart-charging-card.js"),
            cache_headers=False,
        )
        _LOGGER.info("GW Smart Charging custom card registered")
    except Exception as e:
        _LOGGER.error("Failed to register custom card: %s", e)


async def _async_register_panel(hass: HomeAssistant) -> None:
    """Register the panel in Home Assistant sidebar."""
    try:
        await hass.async_add_executor_job(
            frontend.async_register_built_in_panel,
            hass,
            "iframe",
            "GW Smart Charging",
            "mdi:battery-charging-80",
            DOMAIN,
            {"url": f"/api/{DOMAIN}/dashboard"},
            require_admin=False,
        )
        _LOGGER.info("GW Smart Charging panel registered in sidebar")
    except Exception as e:
        _LOGGER.error("Failed to register panel: %s", e)


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN].pop(entry.entry_id, None)
    return unload_ok
