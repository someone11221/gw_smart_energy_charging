from __future__ import annotations

import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_FORECAST_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_GOODWE_SWITCH,
    CONF_PV_POWER_SENSOR,
    CONF_SOC_SENSOR,
    CONF_BATTERY_CAPACITY,
    CONF_MAX_CHARGE_POWER,
    CONF_CHARGE_EFFICIENCY,
    CONF_MIN_RESERVE,
    CONF_ENABLE_AUTOMATION,
    CONF_SWITCH_ON_MEANS_CHARGE,
)


class GWSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for GW Smart Charging."""

    VERSION = 1
    CONNECTION_CLASS = config_entries.CONN_CLASS_LOCAL_POLL

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        """Handle the initial step."""
        errors: dict[str, str] = {}
        if user_input is not None:
            return self.async_create_entry(
                title=user_input.get(CONF_NAME) or "GW Smart Charging", data=user_input
            )

        data_schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="GW Smart Charging"): str,
                vol.Required(CONF_FORECAST_SENSOR, default=""): str,
                vol.Required(CONF_PRICE_SENSOR, default=""): str,
                vol.Optional(CONF_PV_POWER_SENSOR, default=""): str,
                vol.Optional(CONF_GOODWE_SWITCH, default="switch.nabijeni_ze_site"): str,
                vol.Optional(CONF_SOC_SENSOR, default="sensor.battery_state_of_charge"): str,
                vol.Optional(CONF_BATTERY_CAPACITY, default=17): vol.Coerce(float),
                vol.Optional(CONF_MAX_CHARGE_POWER, default=3.7): vol.Coerce(float),
                vol.Optional(CONF_CHARGE_EFFICIENCY, default=0.95): vol.Coerce(float),
                vol.Optional(CONF_MIN_RESERVE, default=10): vol.Coerce(float),
                vol.Optional(CONF_ENABLE_AUTOMATION, default=True): bool,
                vol.Optional(CONF_SWITCH_ON_MEANS_CHARGE, default=True): bool,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)
