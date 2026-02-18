"""Config flow for Smart Battery Charging Controller v3.2.0.

Validates all entity_ids and scripts in real-time during setup.
"""
import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback
from .const import *
from .distribution_tariffs import DISTRIBUTOR_OPTIONS, TARIFF_OPTIONS, BREAKER_OPTIONS

PRICE_PROVIDERS = ["ote", "nanogreen"]
BATTERY_TYPES = ["goodwe", "tesla", "huawei", "generic"]


def _validate_sensor(hass, entity_id: str, label: str, errors: dict,
                     expect_numeric=True, allow_empty=False):
    """Validate sensor exists and returns valid data."""
    if not entity_id or not entity_id.strip():
        if allow_empty:
            return True
        errors["base"] = f"⚠️ {label}: entity_id je prázdné"
        return False
    entity_id = entity_id.strip()
    state = hass.states.get(entity_id)
    if state is None:
        errors["base"] = f"⚠️ {label}: entita '{entity_id}' neexistuje v HA"
        return False
    if state.state in ("unavailable", "unknown"):
        errors["base"] = f"⚠️ {label}: '{entity_id}' je {state.state} — zkontroluj integraci"
        return False
    if expect_numeric:
        try:
            float(state.state)
        except (ValueError, TypeError):
            errors["base"] = f"⚠️ {label}: '{entity_id}' nevrací číslo (stav='{state.state}')"
            return False
    return True


def _validate_script(hass, entity_id: str, label: str, errors: dict):
    """Validate script entity exists."""
    if not entity_id or not entity_id.strip():
        errors["base"] = f"⚠️ {label}: entity_id je prázdné"
        return False
    entity_id = entity_id.strip()
    # Accept both "script.name" and just "name"
    if not entity_id.startswith("script."):
        entity_id = f"script.{entity_id}"
    state = hass.states.get(entity_id)
    if state is None:
        errors["base"] = f"⚠️ {label}: skript '{entity_id}' neexistuje v HA"
        return False
    return True


class SmartChargingConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    def __init__(self):
        self._data = {}

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input:
            # Validate price sensor
            ok = _validate_sensor(self.hass, user_input.get(CONF_PRICE_SENSOR, ""),
                                  "Cenový senzor", errors, expect_numeric=False)
            if ok:
                self._data.update(user_input)
                return await self.async_step_distribution()

        return self.async_show_form(step_id="user", data_schema=vol.Schema({
            vol.Required(CONF_PRICE_PROVIDER, default="ote"): vol.In(PRICE_PROVIDERS),
            vol.Required(CONF_PRICE_SENSOR, default="sensor.current_consumption_price_czk_kwh"): str,
        }), errors=errors)

    async def async_step_distribution(self, user_input=None):
        errors = {}
        if user_input:
            hdo = user_input.get(CONF_HDO_SENSOR, "").strip()
            if hdo:
                _validate_sensor(self.hass, hdo, "HDO senzor", errors, expect_numeric=False)
            # HDO is optional — warn but don't block
            if errors:
                errors = {}  # downgrade to warning, still proceed
            self._data.update(user_input)
            return await self.async_step_battery()

        return self.async_show_form(step_id="distribution", data_schema=vol.Schema({
            vol.Required(CONF_DISTRIBUTOR, default=DEFAULT_DISTRIBUTOR): vol.In(DISTRIBUTOR_OPTIONS),
            vol.Required(CONF_TARIFF, default=DEFAULT_TARIFF): vol.In(TARIFF_OPTIONS),
            vol.Required(CONF_CIRCUIT_BREAKER, default=DEFAULT_CIRCUIT_BREAKER): vol.In(BREAKER_OPTIONS),
            vol.Optional(CONF_HDO_SENSOR, default=DEFAULT_HDO_SENSOR): str,
        }), errors=errors)

    async def async_step_battery(self, user_input=None):
        errors = {}
        if user_input:
            ok = True
            ok = _validate_sensor(self.hass, user_input.get(CONF_SOC_SENSOR, ""),
                                  "SOC senzor", errors) and ok
            if ok:
                ok = _validate_sensor(self.hass, user_input.get(CONF_BATTERY_POWER_SENSOR, ""),
                                      "Senzor výkonu baterie", errors) and ok
            if ok:
                ok = _validate_script(self.hass, user_input.get(CONF_CHARGING_SCRIPT_ON, ""),
                                      "Skript zapnutí nabíjení", errors) and ok
            if ok:
                ok = _validate_script(self.hass, user_input.get(CONF_CHARGING_SCRIPT_OFF, ""),
                                      "Skript vypnutí nabíjení", errors) and ok
            # Optional sensors — validate only if provided
            if ok and user_input.get(CONF_CONSUMPTION_SENSOR):
                _validate_sensor(self.hass, user_input[CONF_CONSUMPTION_SENSOR],
                                 "Senzor spotřeby", errors, allow_empty=True)
            if ok and not errors:
                self._data.update(user_input)
                return await self.async_step_strategy()

        return self.async_show_form(step_id="battery", data_schema=vol.Schema({
            vol.Required(CONF_BATTERY_TYPE, default="goodwe"): vol.In(BATTERY_TYPES),
            vol.Required(CONF_SOC_SENSOR, default="sensor.battery_state_of_charge"): str,
            vol.Required(CONF_BATTERY_POWER_SENSOR, default="sensor.battery_power"): str,
            vol.Required(CONF_BATTERY_CAPACITY, default=DEFAULT_BATTERY_CAPACITY): vol.Coerce(float),
            vol.Required(CONF_CHARGING_SCRIPT_ON, default="script.nabijeni_on"): str,
            vol.Required(CONF_CHARGING_SCRIPT_OFF, default="script.nabijeni_off"): str,
            vol.Optional(CONF_CONSUMPTION_SENSOR, default=""): str,
            vol.Optional(CONF_ENERGY_DASHBOARD_ENTITY, default=""): str,
            vol.Required(CONF_PREDICTION_MODE, default=DEFAULT_PREDICTION_MODE): vol.In(PREDICTION_MODES),
        }), errors=errors)

    async def async_step_strategy(self, user_input=None):
        if user_input:
            self._data.update(user_input)
            return self.async_create_entry(title=f"Smart Battery Charging v{VERSION}", data=self._data)
        return self.async_show_form(step_id="strategy", data_schema=vol.Schema({
            vol.Required(CONF_MIN_SOC_BEFORE_PEAK, default=DEFAULT_MIN_SOC_BEFORE_PEAK):
                vol.All(vol.Coerce(int), vol.Range(min=50, max=100)),
            vol.Required(CONF_TARGET_SOC_FULL, default=DEFAULT_TARGET_SOC_FULL):
                vol.All(vol.Coerce(int), vol.Range(min=50, max=100)),
            vol.Required(CONF_MIN_SOC_SAFETY, default=DEFAULT_MIN_SOC_SAFETY):
                vol.All(vol.Coerce(int), vol.Range(min=5, max=50)),
            vol.Required(CONF_CHARGING_POWER, default=DEFAULT_CHARGING_POWER):
                vol.All(vol.Coerce(float), vol.Range(min=0.5, max=25.0)),
            vol.Required(CONF_FLAT_PRICE_COMPARE, default=DEFAULT_FLAT_PRICE_COMPARE):
                vol.All(vol.Coerce(float), vol.Range(min=0.5, max=15.0)),
            vol.Required(CONF_AUTO_CHARGING, default=True): bool,
        }))

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return SmartChargingOptionsFlow(config_entry)


class SmartChargingOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry):
        pass

    async def async_step_init(self, user_input=None):
        c = self.config_entry.data
        errors = {}

        if user_input:
            # Validate critical sensors
            ok = True
            for key, label, numeric in [
                (CONF_SOC_SENSOR, "SOC senzor", True),
                (CONF_BATTERY_POWER_SENSOR, "Senzor výkonu", True),
                (CONF_PRICE_SENSOR, "Cenový senzor", False),
            ]:
                val = user_input.get(key, "")
                if val and not _validate_sensor(self.hass, val, label, errors, expect_numeric=numeric):
                    ok = False
                    break

            # Validate scripts
            if ok:
                for key, label in [
                    (CONF_CHARGING_SCRIPT_ON, "Skript nabíjení ON"),
                    (CONF_CHARGING_SCRIPT_OFF, "Skript nabíjení OFF"),
                ]:
                    val = user_input.get(key, "")
                    if val and not _validate_script(self.hass, val, label, errors):
                        ok = False
                        break

            if ok:
                new = {**c, **user_input}
                self.hass.config_entries.async_update_entry(self.config_entry, data=new)
                try:
                    coord = self.hass.data.get(DOMAIN, {}).get(self.config_entry.entry_id)
                    if coord:
                        for k, v in user_input.items():
                            coord.config[k] = v
                        if hasattr(coord, 'strategy'):
                            for k, v in user_input.items():
                                coord.strategy.config[k] = v
                        if hasattr(coord, 'hdo_reader') and CONF_HDO_SENSOR in user_input:
                            coord.hdo_reader._sensor = user_input[CONF_HDO_SENSOR]
                        coord.dbg.info("config", "Options updated via UI", changed=list(user_input.keys()))
                except Exception:
                    pass
                return self.async_create_entry(title="", data=user_input)

        return self.async_show_form(step_id="init", data_schema=vol.Schema({
            vol.Required(CONF_DISTRIBUTOR, default=c.get(CONF_DISTRIBUTOR, DEFAULT_DISTRIBUTOR)):
                vol.In(DISTRIBUTOR_OPTIONS),
            vol.Required(CONF_TARIFF, default=c.get(CONF_TARIFF, DEFAULT_TARIFF)):
                vol.In(TARIFF_OPTIONS),
            vol.Required(CONF_CIRCUIT_BREAKER, default=c.get(CONF_CIRCUIT_BREAKER, DEFAULT_CIRCUIT_BREAKER)):
                vol.In(BREAKER_OPTIONS),
            vol.Optional(CONF_HDO_SENSOR, default=c.get(CONF_HDO_SENSOR, DEFAULT_HDO_SENSOR)): str,
            vol.Required(CONF_PREDICTION_MODE, default=c.get(CONF_PREDICTION_MODE, DEFAULT_PREDICTION_MODE)):
                vol.In(PREDICTION_MODES),
            vol.Required(CONF_MIN_SOC_BEFORE_PEAK, default=int(c.get(CONF_MIN_SOC_BEFORE_PEAK, 80))):
                vol.All(vol.Coerce(int), vol.Range(min=50, max=100)),
            vol.Required(CONF_TARGET_SOC_FULL, default=int(c.get(CONF_TARGET_SOC_FULL, 90))):
                vol.All(vol.Coerce(int), vol.Range(min=50, max=100)),
            vol.Required(CONF_CHARGING_POWER, default=float(c.get(CONF_CHARGING_POWER, 5.0))):
                vol.All(vol.Coerce(float), vol.Range(min=0.5, max=25.0)),
            vol.Required(CONF_SOC_SENSOR, default=c.get(CONF_SOC_SENSOR, "")): str,
            vol.Required(CONF_BATTERY_POWER_SENSOR, default=c.get(CONF_BATTERY_POWER_SENSOR, "")): str,
            vol.Required(CONF_PRICE_SENSOR, default=c.get(CONF_PRICE_SENSOR, "")): str,
            vol.Required(CONF_CHARGING_SCRIPT_ON, default=c.get(CONF_CHARGING_SCRIPT_ON, "")): str,
            vol.Required(CONF_CHARGING_SCRIPT_OFF, default=c.get(CONF_CHARGING_SCRIPT_OFF, "")): str,
            vol.Optional(CONF_CONSUMPTION_SENSOR, default=c.get(CONF_CONSUMPTION_SENSOR, "")): str,
            vol.Optional(CONF_ENERGY_DASHBOARD_ENTITY, default=c.get(CONF_ENERGY_DASHBOARD_ENTITY, "")): str,
            vol.Required(CONF_FLAT_PRICE_COMPARE, default=float(c.get(CONF_FLAT_PRICE_COMPARE, DEFAULT_FLAT_PRICE_COMPARE))):
                vol.All(vol.Coerce(float), vol.Range(min=0.5, max=15.0)),
            vol.Required(CONF_AUTO_CHARGING, default=bool(c.get(CONF_AUTO_CHARGING, True))): bool,
        }), errors=errors)
