from __future__ import annotations

import voluptuous as vol
from typing import Any

from homeassistant import config_entries
from homeassistant.const import CONF_NAME

from .const import (
    DOMAIN,
    CONF_FORECAST_SENSOR,
    CONF_PRICE_SENSOR,
    CONF_LOAD_SENSOR,
    CONF_DAILY_LOAD_SENSOR,
    CONF_PV_POWER_SENSOR,
    CONF_GOODWE_SWITCH,
    CONF_SOC_SENSOR,
    CONF_BATTERY_CAPACITY,
    CONF_MAX_CHARGE_POWER,
    CONF_CHARGE_EFFICIENCY,
    CONF_MIN_SOC,
    CONF_MAX_SOC,
    CONF_TARGET_SOC,
    CONF_ALWAYS_CHARGE_PRICE,
    CONF_NEVER_CHARGE_PRICE,
    CONF_ENABLE_AUTOMATION,
    CONF_SWITCH_ON_MEANS_CHARGE,
    DEFAULT_BATTERY_CAPACITY,
    DEFAULT_MAX_CHARGE_POWER,
    DEFAULT_CHARGE_EFFICIENCY,
    DEFAULT_MIN_SOC,
    DEFAULT_MAX_SOC,
    DEFAULT_TARGET_SOC,
    DEFAULT_ALWAYS_CHARGE_PRICE,
    DEFAULT_NEVER_CHARGE_PRICE,
)


class GWSmartConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for GW Smart Charging."""

    VERSION = 1

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
                vol.Required(CONF_FORECAST_SENSOR, default="sensor.energy_production_d2"): str,
                vol.Required(CONF_PRICE_SENSOR, default="sensor.current_consumption_price_czk_kwh"): str,
                vol.Required(CONF_LOAD_SENSOR, default="sensor.house_consumption"): str,
                vol.Optional(CONF_DAILY_LOAD_SENSOR, default="sensor.house_consumption_daily"): str,
                vol.Optional(CONF_PV_POWER_SENSOR, default=""): str,
                vol.Optional(CONF_GOODWE_SWITCH, default="switch.nabijeni_ze_site"): str,
                vol.Optional(CONF_SOC_SENSOR, default="sensor.battery_state_of_charge"): str,
                vol.Optional(CONF_BATTERY_CAPACITY, default=DEFAULT_BATTERY_CAPACITY): vol.Coerce(float),
                vol.Optional(CONF_MAX_CHARGE_POWER, default=DEFAULT_MAX_CHARGE_POWER): vol.Coerce(float),
                vol.Optional(CONF_CHARGE_EFFICIENCY, default=DEFAULT_CHARGE_EFFICIENCY): vol.Coerce(float),
                vol.Optional(CONF_MIN_SOC, default=DEFAULT_MIN_SOC): vol.Coerce(float),
                vol.Optional(CONF_MAX_SOC, default=DEFAULT_MAX_SOC): vol.Coerce(float),
                vol.Optional(CONF_TARGET_SOC, default=DEFAULT_TARGET_SOC): vol.Coerce(float),
                vol.Optional(CONF_ALWAYS_CHARGE_PRICE, default=DEFAULT_ALWAYS_CHARGE_PRICE): vol.Coerce(float),
                vol.Optional(CONF_NEVER_CHARGE_PRICE, default=DEFAULT_NEVER_CHARGE_PRICE): vol.Coerce(float),
                vol.Optional(CONF_ENABLE_AUTOMATION, default=True): bool,
                vol.Optional(CONF_SWITCH_ON_MEANS_CHARGE, default=True): bool,
            }
        )

        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry):
        """Get the options flow for this handler."""
        return GWSmartOptionsFlow(config_entry)


class GWSmartOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for reconfiguring sensors."""

    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        """Initialize options flow."""
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        """Manage the options for reconfiguring sensors."""
        errors: dict[str, str] = {}
        
        if user_input is not None:
            # Update the config entry with new values
            self.hass.config_entries.async_update_entry(
                self.config_entry, data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(title="", data={})

        # Get current values from config entry
        current_config = self.config_entry.data

        data_schema = vol.Schema(
            {
                vol.Required(
                    CONF_NAME, 
                    default=current_config.get(CONF_NAME, "GW Smart Charging")
                ): str,
                vol.Required(
                    CONF_FORECAST_SENSOR, 
                    default=current_config.get(CONF_FORECAST_SENSOR, "sensor.energy_production_d2")
                ): str,
                vol.Required(
                    CONF_PRICE_SENSOR, 
                    default=current_config.get(CONF_PRICE_SENSOR, "sensor.current_consumption_price_czk_kwh")
                ): str,
                vol.Required(
                    CONF_LOAD_SENSOR, 
                    default=current_config.get(CONF_LOAD_SENSOR, "sensor.house_consumption")
                ): str,
                vol.Optional(
                    CONF_DAILY_LOAD_SENSOR, 
                    default=current_config.get(CONF_DAILY_LOAD_SENSOR, "sensor.house_consumption_daily")
                ): str,
                vol.Optional(
                    CONF_PV_POWER_SENSOR, 
                    default=current_config.get(CONF_PV_POWER_SENSOR, "")
                ): str,
                vol.Optional(
                    CONF_GOODWE_SWITCH, 
                    default=current_config.get(CONF_GOODWE_SWITCH, "switch.nabijeni_ze_site")
                ): str,
                vol.Optional(
                    CONF_SOC_SENSOR, 
                    default=current_config.get(CONF_SOC_SENSOR, "sensor.battery_state_of_charge")
                ): str,
                vol.Optional(
                    CONF_BATTERY_CAPACITY, 
                    default=current_config.get(CONF_BATTERY_CAPACITY, DEFAULT_BATTERY_CAPACITY)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MAX_CHARGE_POWER, 
                    default=current_config.get(CONF_MAX_CHARGE_POWER, DEFAULT_MAX_CHARGE_POWER)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CHARGE_EFFICIENCY, 
                    default=current_config.get(CONF_CHARGE_EFFICIENCY, DEFAULT_CHARGE_EFFICIENCY)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MIN_SOC, 
                    default=current_config.get(CONF_MIN_SOC, DEFAULT_MIN_SOC)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_MAX_SOC, 
                    default=current_config.get(CONF_MAX_SOC, DEFAULT_MAX_SOC)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_TARGET_SOC, 
                    default=current_config.get(CONF_TARGET_SOC, DEFAULT_TARGET_SOC)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_ALWAYS_CHARGE_PRICE, 
                    default=current_config.get(CONF_ALWAYS_CHARGE_PRICE, DEFAULT_ALWAYS_CHARGE_PRICE)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_NEVER_CHARGE_PRICE, 
                    default=current_config.get(CONF_NEVER_CHARGE_PRICE, DEFAULT_NEVER_CHARGE_PRICE)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_ENABLE_AUTOMATION, 
                    default=current_config.get(CONF_ENABLE_AUTOMATION, True)
                ): bool,
                vol.Optional(
                    CONF_SWITCH_ON_MEANS_CHARGE, 
                    default=current_config.get(CONF_SWITCH_ON_MEANS_CHARGE, True)
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init", 
            data_schema=data_schema, 
            errors=errors,
            description_placeholders={
                "info": "Reconfigure sensor entities and parameters. Target SOC: desired battery charge level (%), Always charge below: price threshold (CZK/kWh), Never charge above: price limit (CZK/kWh)"
            }
        )
