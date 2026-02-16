"""Constants for Smart Battery Charging Controller v3.0.1."""

DOMAIN = "gw_smart_charging"
VERSION = "3.0.1"

# Configuration keys
CONF_PRICE_PROVIDER = "price_provider"
CONF_PRICE_SENSOR = "price_sensor"
CONF_BATTERY_TYPE = "battery_type"
CONF_SOC_SENSOR = "soc_sensor"
CONF_BATTERY_POWER_SENSOR = "battery_power_sensor"
CONF_BATTERY_CAPACITY = "battery_capacity"
CONF_CHARGING_SCRIPT_ON = "charging_script_on"
CONF_CHARGING_SCRIPT_OFF = "charging_script_off"
CONF_TODAY_CHARGE_SENSOR = "today_charge_sensor"
CONF_TODAY_DISCHARGE_SENSOR = "today_discharge_sensor"

# Strategy parameters
CONF_MIN_SOC_BEFORE_PEAK = "min_soc_before_peak"
CONF_TARGET_SOC_FULL = "target_soc_full"
CONF_MIN_SOC_SAFETY = "min_soc_safety"
CONF_MAX_SOC_LIMIT = "max_soc_limit"
CONF_CHARGING_POWER = "charging_power"
CONF_CHARGING_EFFICIENCY = "charging_efficiency"

# Price thresholds
CONF_PEAK_PRICE_THRESHOLD = "peak_price_threshold"
CONF_CHEAP_PRICE_THRESHOLD = "cheap_price_threshold"

# Timing
CONF_LOOKAHEAD_HOURS = "lookahead_hours"
CONF_PEAK_PREPARATION_HOURS = "peak_preparation_hours"

# Control
CONF_AUTO_CHARGING = "auto_charging"
CONF_TEST_MODE = "test_mode"

# Sensor names
SENSOR_CHARGING_PLAN = "charging_plan"
SENSOR_BATTERY_STATUS = "battery_status"
SENSOR_PRICE_FORECAST = "price_forecast"
SENSOR_NEXT_CHARGING = "next_charging"
SENSOR_STATISTICS = "statistics"
SENSOR_DIAGNOSTICS = "diagnostics"

# Switch names
SWITCH_AUTO_CHARGING = "auto_charging"

# Service names
SERVICE_FORCE_PLAN_UPDATE = "force_plan_update"
SERVICE_GET_CHARGING_SCHEDULE = "get_charging_schedule"

# Default values
DEFAULT_BATTERY_CAPACITY = 17.0
DEFAULT_CHARGING_POWER = 5.0
DEFAULT_CHARGING_EFFICIENCY = 0.95
DEFAULT_MIN_SOC_BEFORE_PEAK = 80
DEFAULT_TARGET_SOC_FULL = 95
DEFAULT_MIN_SOC_SAFETY = 20
DEFAULT_MAX_SOC_LIMIT = 100
DEFAULT_PEAK_PRICE_THRESHOLD = 0.75
DEFAULT_CHEAP_PRICE_THRESHOLD = 0.35
DEFAULT_LOOKAHEAD_HOURS = 24
DEFAULT_PEAK_PREPARATION_HOURS = 4
