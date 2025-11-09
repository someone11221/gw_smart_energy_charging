# Updated coordinator: adds ISO timestamps for target day and a simple forecast confidence metric.

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional, Tuple
from datetime import timedelta, datetime, date, time as dt_time

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN,
    CONF_FORECAST_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_LOAD_SENSOR,
    CONF_SOC_SENSOR,
    CONF_BATTERY_CAPACITY,
    CONF_MAX_CHARGE_POWER,
    CONF_CHARGE_EFFICIENCY,
    CONF_MIN_RESERVE,
)

_LOGGER = logging.getLogger(__name__)


class GWSmartCoordinator(DataUpdateCoordinator):
    """Coordinator that reads forecast, price and load sensors and produces a charging schedule."""

    def __init__(self, hass: HomeAssistant, entry: ConfigEntry) -> None:
        super().__init__(
            hass,
            _LOGGER,
            name="gw_smart_charging_coordinator",
            update_interval=timedelta(minutes=5),
        )
        self.entry = entry
        self.config: dict[str, Any] = entry.data or {}
        # cache to accumulate cumulative daily deltas while running
        self._last_daily_cumulative: Optional[float] = None
        self._last_daily_date: Optional[date] = None

    async def _async_update_data(self) -> dict[str, Any]:
        """Fetch and normalize forecast, price and load data and compute schedule."""
        try:
            forecast_sensor = self.config.get(CONF_FORECAST_SENSOR)
            price_sensor = self.config.get(CONF_PRICE_SENSOR)
            load_sensor =
