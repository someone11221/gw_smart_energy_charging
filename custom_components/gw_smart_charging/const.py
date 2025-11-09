# Constants for GW Smart Charging

DOMAIN = "gw_smart_charging"
PLATFORMS = ["sensor", "switch"]

DEFAULT_NAME = "GW Smart Charging"

# Sensor configuration
CONF_FORECAST_SENSOR = "forecast_sensor"
CONF_PRICE_SENSOR = "price_sensor"
CONF_LOAD_SENSOR = "load_sensor"
CONF_DAILY_LOAD_SENSOR = "daily_load_sensor"
CONF_GOODWE_SWITCH = "goodwe_switch"
CONF_PV_POWER_SENSOR = "pv_power_sensor"
CONF_SOC_SENSOR = "soc_sensor"

# Battery configuration
CONF_BATTERY_CAPACITY = "battery_capacity_kwh"
CONF_MAX_CHARGE_POWER = "max_charge_power_kw"
CONF_CHARGE_EFFICIENCY = "charge_efficiency"
CONF_MIN_SOC = "min_soc_pct"
CONF_MAX_SOC = "max_soc_pct"
CONF_TARGET_SOC = "target_soc_pct"

# Price thresholds
CONF_ALWAYS_CHARGE_PRICE = "always_charge_price"
CONF_NEVER_CHARGE_PRICE = "never_charge_price"

# Automation
CONF_ENABLE_AUTOMATION = "enable_automation"
CONF_SWITCH_ON_MEANS_CHARGE = "switch_on_means_charge"

# Default values
DEFAULT_BATTERY_CAPACITY = 17.0
DEFAULT_MAX_CHARGE_POWER = 3.7
DEFAULT_CHARGE_EFFICIENCY = 0.95
DEFAULT_MIN_SOC = 10.0
DEFAULT_MAX_SOC = 95.0
DEFAULT_TARGET_SOC = 90.0
DEFAULT_ALWAYS_CHARGE_PRICE = 1.5
DEFAULT_NEVER_CHARGE_PRICE = 4.0
