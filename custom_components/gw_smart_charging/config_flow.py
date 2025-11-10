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
    CONF_CHARGING_ON_SCRIPT,
    CONF_CHARGING_OFF_SCRIPT,
    CONF_SOC_SENSOR,
    CONF_BATTERY_POWER_SENSOR,
    CONF_GRID_IMPORT_SENSOR,
    CONF_TODAY_BATTERY_CHARGE_SENSOR,
    CONF_TODAY_BATTERY_DISCHARGE_SENSOR,
    CONF_NANOGREEN_CHEAPEST_SENSOR,
    CONF_ADDITIONAL_SWITCHES,
    CONF_SWITCH_PRICE_THRESHOLD,
    CONF_BATTERY_CAPACITY,
    CONF_MAX_CHARGE_POWER,
    CONF_CHARGE_EFFICIENCY,
    CONF_MIN_SOC,
    CONF_MAX_SOC,
    CONF_TARGET_SOC,
    CONF_ALWAYS_CHARGE_PRICE,
    CONF_NEVER_CHARGE_PRICE,
    CONF_PRICE_HYSTERESIS,
    CONF_CRITICAL_HOURS_START,
    CONF_CRITICAL_HOURS_END,
    CONF_CRITICAL_HOURS_SOC,
    CONF_ENABLE_ML_PREDICTION,
    CONF_ENABLE_AUTOMATION,
    CONF_SWITCH_ON_MEANS_CHARGE,
    CONF_TEST_MODE,
    CONF_CHARGING_STRATEGY,
    CONF_LANGUAGE,
    CONF_FULL_HOUR_CHARGING,
    STRATEGY_DYNAMIC,
    STRATEGY_4_LOWEST,
    STRATEGY_6_LOWEST,
    STRATEGY_NANOGREEN_ONLY,
    STRATEGY_PRICE_THRESHOLD,
    STRATEGY_ADAPTIVE_SMART,
    STRATEGY_SOLAR_PRIORITY,
    STRATEGY_PEAK_SHAVING,
    STRATEGY_TOU_OPTIMIZED,
    DEFAULT_BATTERY_CAPACITY,
    DEFAULT_MAX_CHARGE_POWER,
    DEFAULT_CHARGE_EFFICIENCY,
    DEFAULT_MIN_SOC,
    DEFAULT_MAX_SOC,
    DEFAULT_TARGET_SOC,
    DEFAULT_ALWAYS_CHARGE_PRICE,
    DEFAULT_NEVER_CHARGE_PRICE,
    DEFAULT_PRICE_HYSTERESIS,
    DEFAULT_CRITICAL_HOURS_START,
    DEFAULT_CRITICAL_HOURS_END,
    DEFAULT_CRITICAL_HOURS_SOC,
    DEFAULT_ENABLE_ML_PREDICTION,
    DEFAULT_SWITCH_PRICE_THRESHOLD,
    DEFAULT_CHARGING_STRATEGY,
    DEFAULT_LANGUAGE,
    DEFAULT_FULL_HOUR_CHARGING,
    LANGUAGE_CS,
    LANGUAGE_EN,
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
                vol.Optional(CONF_BATTERY_POWER_SENSOR, default="sensor.battery_power"): str,
                vol.Optional(CONF_GRID_IMPORT_SENSOR, default="sensor.energy_buy"): str,
                vol.Optional(CONF_TODAY_BATTERY_CHARGE_SENSOR, default="sensor.today_battery_charge"): str,
                vol.Optional(CONF_TODAY_BATTERY_DISCHARGE_SENSOR, default="sensor.today_battery_discharge"): str,
                vol.Optional(CONF_NANOGREEN_CHEAPEST_SENSOR, default=""): str,
                vol.Optional(CONF_ADDITIONAL_SWITCHES, default=""): str,
                vol.Optional(CONF_SWITCH_PRICE_THRESHOLD, default=DEFAULT_SWITCH_PRICE_THRESHOLD): vol.Coerce(float),
                vol.Optional(CONF_CHARGING_ON_SCRIPT, default="script.nabijeni_on"): str,
                vol.Optional(CONF_CHARGING_OFF_SCRIPT, default="script.nabijeni_off"): str,
                vol.Optional(CONF_SOC_SENSOR, default="sensor.battery_state_of_charge"): str,
                vol.Optional(CONF_BATTERY_CAPACITY, default=DEFAULT_BATTERY_CAPACITY): vol.Coerce(float),
                vol.Optional(CONF_MAX_CHARGE_POWER, default=DEFAULT_MAX_CHARGE_POWER): vol.Coerce(float),
                vol.Optional(CONF_CHARGE_EFFICIENCY, default=DEFAULT_CHARGE_EFFICIENCY): vol.Coerce(float),
                vol.Optional(CONF_MIN_SOC, default=DEFAULT_MIN_SOC): vol.Coerce(float),
                vol.Optional(CONF_MAX_SOC, default=DEFAULT_MAX_SOC): vol.Coerce(float),
                vol.Optional(CONF_TARGET_SOC, default=DEFAULT_TARGET_SOC): vol.Coerce(float),
                vol.Optional(CONF_ALWAYS_CHARGE_PRICE, default=DEFAULT_ALWAYS_CHARGE_PRICE): vol.Coerce(float),
                vol.Optional(CONF_NEVER_CHARGE_PRICE, default=DEFAULT_NEVER_CHARGE_PRICE): vol.Coerce(float),
                vol.Optional(CONF_PRICE_HYSTERESIS, default=DEFAULT_PRICE_HYSTERESIS): vol.Coerce(float),
                vol.Optional(CONF_CRITICAL_HOURS_START, default=DEFAULT_CRITICAL_HOURS_START): vol.Coerce(int),
                vol.Optional(CONF_CRITICAL_HOURS_END, default=DEFAULT_CRITICAL_HOURS_END): vol.Coerce(int),
                vol.Optional(CONF_CRITICAL_HOURS_SOC, default=DEFAULT_CRITICAL_HOURS_SOC): vol.Coerce(float),
                vol.Optional(CONF_CHARGING_STRATEGY, default=DEFAULT_CHARGING_STRATEGY): vol.In([
                    STRATEGY_DYNAMIC,
                    STRATEGY_4_LOWEST,
                    STRATEGY_6_LOWEST,
                    STRATEGY_NANOGREEN_ONLY,
                    STRATEGY_PRICE_THRESHOLD,
                    STRATEGY_ADAPTIVE_SMART,
                    STRATEGY_SOLAR_PRIORITY,
                    STRATEGY_PEAK_SHAVING,
                    STRATEGY_TOU_OPTIMIZED,
                ]),
                vol.Optional(CONF_LANGUAGE, default=DEFAULT_LANGUAGE): vol.In([LANGUAGE_CS, LANGUAGE_EN]),
                vol.Optional(CONF_FULL_HOUR_CHARGING, default=DEFAULT_FULL_HOUR_CHARGING): bool,
                vol.Optional(CONF_ENABLE_ML_PREDICTION, default=DEFAULT_ENABLE_ML_PREDICTION): bool,
                vol.Optional(CONF_ENABLE_AUTOMATION, default=True): bool,
                vol.Optional(CONF_SWITCH_ON_MEANS_CHARGE, default=True): bool,
                vol.Optional(CONF_TEST_MODE, default=False): bool,
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
                    CONF_BATTERY_POWER_SENSOR, 
                    default=current_config.get(CONF_BATTERY_POWER_SENSOR, "sensor.battery_power")
                ): str,
                vol.Optional(
                    CONF_GRID_IMPORT_SENSOR, 
                    default=current_config.get(CONF_GRID_IMPORT_SENSOR, "sensor.energy_buy")
                ): str,
                vol.Optional(
                    CONF_TODAY_BATTERY_CHARGE_SENSOR, 
                    default=current_config.get(CONF_TODAY_BATTERY_CHARGE_SENSOR, "sensor.today_battery_charge")
                ): str,
                vol.Optional(
                    CONF_TODAY_BATTERY_DISCHARGE_SENSOR, 
                    default=current_config.get(CONF_TODAY_BATTERY_DISCHARGE_SENSOR, "sensor.today_battery_discharge")
                ): str,
                vol.Optional(
                    CONF_NANOGREEN_CHEAPEST_SENSOR,
                    default=current_config.get(CONF_NANOGREEN_CHEAPEST_SENSOR, "")
                ): str,
                vol.Optional(
                    CONF_ADDITIONAL_SWITCHES,
                    default=current_config.get(CONF_ADDITIONAL_SWITCHES, "")
                ): str,
                vol.Optional(
                    CONF_SWITCH_PRICE_THRESHOLD,
                    default=current_config.get(CONF_SWITCH_PRICE_THRESHOLD, DEFAULT_SWITCH_PRICE_THRESHOLD)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CHARGING_ON_SCRIPT, 
                    default=current_config.get(CONF_CHARGING_ON_SCRIPT, "script.nabijeni_on")
                ): str,
                vol.Optional(
                    CONF_CHARGING_OFF_SCRIPT, 
                    default=current_config.get(CONF_CHARGING_OFF_SCRIPT, "script.nabijeni_off")
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
                    CONF_PRICE_HYSTERESIS, 
                    default=current_config.get(CONF_PRICE_HYSTERESIS, DEFAULT_PRICE_HYSTERESIS)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CRITICAL_HOURS_START, 
                    default=current_config.get(CONF_CRITICAL_HOURS_START, DEFAULT_CRITICAL_HOURS_START)
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_CRITICAL_HOURS_END, 
                    default=current_config.get(CONF_CRITICAL_HOURS_END, DEFAULT_CRITICAL_HOURS_END)
                ): vol.Coerce(int),
                vol.Optional(
                    CONF_CRITICAL_HOURS_SOC, 
                    default=current_config.get(CONF_CRITICAL_HOURS_SOC, DEFAULT_CRITICAL_HOURS_SOC)
                ): vol.Coerce(float),
                vol.Optional(
                    CONF_CHARGING_STRATEGY,
                    default=current_config.get(CONF_CHARGING_STRATEGY, DEFAULT_CHARGING_STRATEGY)
                ): vol.In([
                    STRATEGY_DYNAMIC,
                    STRATEGY_4_LOWEST,
                    STRATEGY_6_LOWEST,
                    STRATEGY_NANOGREEN_ONLY,
                    STRATEGY_PRICE_THRESHOLD,
                    STRATEGY_ADAPTIVE_SMART,
                    STRATEGY_SOLAR_PRIORITY,
                    STRATEGY_PEAK_SHAVING,
                    STRATEGY_TOU_OPTIMIZED,
                ]),
                vol.Optional(
                    CONF_LANGUAGE,
                    default=current_config.get(CONF_LANGUAGE, DEFAULT_LANGUAGE)
                ): vol.In([LANGUAGE_CS, LANGUAGE_EN]),
                vol.Optional(
                    CONF_FULL_HOUR_CHARGING,
                    default=current_config.get(CONF_FULL_HOUR_CHARGING, DEFAULT_FULL_HOUR_CHARGING)
                ): bool,
                vol.Optional(
                    CONF_ENABLE_ML_PREDICTION, 
                    default=current_config.get(CONF_ENABLE_ML_PREDICTION, DEFAULT_ENABLE_ML_PREDICTION)
                ): bool,
                vol.Optional(
                    CONF_ENABLE_AUTOMATION, 
                    default=current_config.get(CONF_ENABLE_AUTOMATION, True)
                ): bool,
                vol.Optional(
                    CONF_SWITCH_ON_MEANS_CHARGE, 
                    default=current_config.get(CONF_SWITCH_ON_MEANS_CHARGE, True)
                ): bool,
                vol.Optional(
                    CONF_TEST_MODE,
                    default=current_config.get(CONF_TEST_MODE, False)
                ): bool,
            }
        )

        return self.async_show_form(
            step_id="init", 
            data_schema=data_schema, 
            errors=errors,
            description_placeholders={
                "info": "Reconfigure sensors and parameters. Hysteresis: ±% buffer around price thresholds. Critical hours: maintain higher SOC during specified hours (e.g., 17-21 for evening peak). ML prediction: learn from historical consumption patterns."
            }
        )
