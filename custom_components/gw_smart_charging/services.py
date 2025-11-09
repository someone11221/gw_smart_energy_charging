from __future__ import annotations

import logging

from homeassistant.core import HomeAssistant, ServiceCall

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_OPTIMIZE = "optimize_now"
SERVICE_APPLY = "apply_schedule_now"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register services for the integration (placeholders)."""

    async def _optimize(call: ServiceCall) -> None:
        _LOGGER.info("Service optimize_now called: %s", call.data)
        # placeholder - trigger immediate recalculation
        # Real implementation should call coordinator methods / algorithms.

    async def _apply(call: ServiceCall) -> None:
        _LOGGER.info("Service apply_schedule_now called: %s", call.data)
        # placeholder - apply schedule to switches

    hass.services.async_register(DOMAIN, SERVICE_OPTIMIZE, _optimize)
    hass.services.async_register(DOMAIN, SERVICE_APPLY, _apply)
