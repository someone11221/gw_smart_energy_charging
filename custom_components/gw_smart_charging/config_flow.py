"""Config flow for Smart Battery Charging Controller v3.0.1."""
from typing import Any, Dict, Optional
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import callback
import homeassistant.helpers.config_validation as cv

from .const import (
    DOMAIN,
    CONF_PRICE_PROVIDER,
    CONF_PRICE_SENSOR,
    CONF_BATTERY_TYPE,
    CONF_SOC_SENSOR,
    CONF_BATTERY_POWER_SENSOR,
    CONF_BATTERY_CAPACITY,
    CONF_CHARGING_SCRIPT_ON,
    CONF_CHARGING_SCRIPT_OFF,
    CONF_MIN_SOC_BEFORE_PEAK,
    CONF_TARGET_SOC_FULL,
    CONF_MIN_SOC_SAFETY,
    CONF_CHARGING_POWER,
    CONF_AUTO_CHARGING,
)

PRICE_PROVIDERS = ["ote", "nanogreen", "nordpool", "entsoe"]
BATTERY_TYPES = ["goodwe", "tesla", "huawei", "generic"]


class SmartChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle config flow for Smart Battery Charging."""
    
    VERSION = 1
    
    async def async_step_user(self, user_input: Optional[Dict[str, Any]] = None):
        """Handle the initial step - price provider selection."""
        errors = {}
        
        if user_input is not None:
            return await self.async_step_battery(user_input)
        
        data_schema = vol.Schema({
            vol.Required(CONF_PRICE_PROVIDER, default="ote"): vol.In(PRICE_PROVIDERS),
            vol.Required(CONF_PRICE_SENSOR, default="sensor.current_consumption_price_czk_kwh"): str,
        })
        
        return self.async_show_form(
            step_id="user",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "info": "Vyberte poskytovatele spotových cen elektřiny"
            }
        )
    
    async def async_step_battery(self, user_input: Dict[str, Any]):
        """Configure battery controller."""
        if "price_provider" in user_input:
            # Store price provider config
            self._price_config = user_input
        
        errors = {}
        
        if user_input is not None and "battery_type" in user_input:
            # Combine all config
            config = {**self._price_config, **user_input}
            return await self.async_step_strategy(config)
        
        data_schema = vol.Schema({
            vol.Required(CONF_BATTERY_TYPE, default="goodwe"): vol.In(BATTERY_TYPES),
            vol.Required(CONF_SOC_SENSOR, default="sensor.battery_state_of_charge"): str,
            vol.Required(CONF_BATTERY_POWER_SENSOR, default="sensor.battery_power"): str,
            vol.Required(CONF_BATTERY_CAPACITY, default=17.0): vol.Coerce(float),
            vol.Required(CONF_CHARGING_SCRIPT_ON, default="script.nabijeni_on"): str,
            vol.Required(CONF_CHARGING_SCRIPT_OFF, default="script.nabijeni_off"): str,
        })
        
        return self.async_show_form(
            step_id="battery",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "info": "Konfigurace bateriového systému a řídicích skriptů"
            }
        )
    
    async def async_step_strategy(self, user_input: Dict[str, Any]):
        """Configure charging strategy parameters."""
        if "battery_type" in user_input:
            # Store battery config
            self._battery_config = user_input
        
        errors = {}
        
        if user_input is not None and "min_soc_before_peak" in user_input:
            # Combine all config
            final_config = {**self._battery_config, **user_input}
            
            # Create entry
            return self.async_create_entry(
                title="Smart Battery Charging v3.0.1",
                data=final_config
            )
        
        data_schema = vol.Schema({
            vol.Required(CONF_MIN_SOC_BEFORE_PEAK, default=80): vol.All(
                vol.Coerce(int), vol.Range(min=50, max=100)
            ),
            vol.Required(CONF_TARGET_SOC_FULL, default=95): vol.All(
                vol.Coerce(int), vol.Range(min=80, max=100)
            ),
            vol.Required(CONF_MIN_SOC_SAFETY, default=20): vol.All(
                vol.Coerce(int), vol.Range(min=10, max=50)
            ),
            vol.Required(CONF_CHARGING_POWER, default=5.0): vol.All(
                vol.Coerce(float), vol.Range(min=1.0, max=20.0)
            ),
            vol.Required(CONF_AUTO_CHARGING, default=True): bool,
        })
        
        return self.async_show_form(
            step_id="strategy",
            data_schema=data_schema,
            errors=errors,
            description_placeholders={
                "info": (
                    "⚡ Min SOC před peakem: Minimální nabití baterie před drahými hodinami\n"
                    "🔋 Cílové SOC: Úroveň plného nabití při velmi levných cenách\n"
                    "🛡️ Bezpečnostní minimum: SOC nikdy neklesne pod tuto hodnotu\n"
                    "⚙️ Nabíjecí výkon: Maximální výkon nabíjení v kW"
                )
            }
        )
    
    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        """Get options flow handler."""
        return SmartChargingOptionsFlow(config_entry)


class SmartChargingOptionsFlow(config_entries.OptionsFlow):
    """Handle options flow for Smart Battery Charging."""
    
    def __init__(self, config_entry):
        """Initialize options flow."""
        self.config_entry = config_entry
    
    async def async_step_init(self, user_input: Optional[Dict[str, Any]] = None):
        """Manage options."""
        if user_input is not None:
            # Update config entry
            self.hass.config_entries.async_update_entry(
                self.config_entry,
                data={**self.config_entry.data, **user_input}
            )
            return self.async_create_entry(title="", data={})
        
        current = self.config_entry.data
        
        data_schema = vol.Schema({
            vol.Required(
                CONF_MIN_SOC_BEFORE_PEAK,
                default=current.get(CONF_MIN_SOC_BEFORE_PEAK, 80)
            ): vol.All(vol.Coerce(int), vol.Range(min=50, max=100)),
            
            vol.Required(
                CONF_TARGET_SOC_FULL,
                default=current.get(CONF_TARGET_SOC_FULL, 95)
            ): vol.All(vol.Coerce(int), vol.Range(min=80, max=100)),
            
            vol.Required(
                CONF_MIN_SOC_SAFETY,
                default=current.get(CONF_MIN_SOC_SAFETY, 20)
            ): vol.All(vol.Coerce(int), vol.Range(min=10, max=50)),
            
            vol.Required(
                CONF_CHARGING_POWER,
                default=current.get(CONF_CHARGING_POWER, 5.0)
            ): vol.All(vol.Coerce(float), vol.Range(min=1.0, max=20.0)),
            
            vol.Required(
                CONF_AUTO_CHARGING,
                default=current.get(CONF_AUTO_CHARGING, True)
            ): bool,
        })
        
        return self.async_show_form(
            step_id="init",
            data_schema=data_schema,
            description_placeholders={
                "info": "Upravte parametry nabíjecí strategie"
            }
        )
