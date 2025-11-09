from __future__ import annotations

import logging
from typing import Any

from datetime import timedelta

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

_LOGGER = logging.getLogger(__name__)


class GWSmartCoordinator(DataUpdateCoordinator):
    """Simple coordinator for GW Smart Charging (placeholder)."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="gw_smart_charging_coordinator",
            update_interval=timedelta(minutes=5),
        )
        self.entry = entry
        # store config in data for sensors/services to use
        self.config: dict[str, Any] = entry.data or {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch data from sources (placeholder). Replace with real implementation."""
        try:
            # TODO: implement actual fetch from sensors / GoodWe etc.
            # Return minimal structure used by sensors (can be extended)
            return {
                "status": "ok",
                "forecast": {},
                "prices": {},
                "last_update": self.hass.time(),
            }
        except Exception as err:
            raise UpdateFailed(err) from err
