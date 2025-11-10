"""Dashboard panel for GW Smart Charging integration."""
from __future__ import annotations

import logging
from typing import Any

from homeassistant.components import frontend
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity_component import EntityComponent

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


async def async_setup_panel(hass: HomeAssistant) -> None:
    """Set up the GW Smart Charging panel."""
    
    # Register the panel
    await hass.async_add_executor_job(
        frontend.async_register_built_in_panel,
        hass,
        "iframe",
        "GW Smart Charging",
        "mdi:battery-charging",
        DOMAIN,
        {"url": f"/api/{DOMAIN}/dashboard"},
        require_admin=False,
    )
    
    _LOGGER.info("GW Smart Charging panel registered")


@callback
def async_unload_panel(hass: HomeAssistant) -> None:
    """Unload the GW Smart Charging panel."""
    frontend.async_remove_panel(hass, DOMAIN)
