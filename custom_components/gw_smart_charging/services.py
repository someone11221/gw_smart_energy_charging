from __future__ import annotations
import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

async def async_setup_services(hass: HomeAssistant):
    hass.services.async_register(DOMAIN, "optimize_now", _handle_optimize_now)
    hass.services.async_register(DOMAIN, "apply_schedule_now", _handle_apply_schedule_now)

async def _handle_optimize_now(call: ServiceCall):
    hass = call.hass
    for entry_id, coord in hass.data.get(DOMAIN, {}).items():
        await coord.async_request_refresh()

async def _handle_apply_schedule_now(call: ServiceCall):
    hass = call.hass
    for entry_id, coord in hass.data.get(DOMAIN, {}).items():
        await coord.apply_current_hour()
