"""Constants for Smart Battery Charging Controller v3.2.0."""

DOMAIN = "gw_smart_charging"
VERSION = "3.2.0"

# ── Config keys ─────────────────────────────────────────────
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

# Distribution
CONF_DISTRIBUTOR = "distributor"
CONF_TARIFF = "tariff"
CONF_CIRCUIT_BREAKER = "circuit_breaker"

# HDO signal (v3.2.0)
CONF_HDO_SENSOR = "hdo_sensor"
DEFAULT_HDO_SENSOR = "sensor.egdtar"

# Consumption prediction
CONF_CONSUMPTION_SENSOR = "consumption_sensor"
CONF_ENERGY_DASHBOARD_ENTITY = "energy_dashboard_entity"
CONF_PREDICTION_MODE = "prediction_mode"
CONF_HISTORY_DAYS = "history_days"

PREDICTION_MODES = {
    "fixed": "Fixní profil (ruční spotřeba)",
    "adaptive": "Adaptivní (učí se z historie)",
}

# Strategy
CONF_MIN_SOC_BEFORE_PEAK = "min_soc_before_peak"
CONF_TARGET_SOC_FULL = "target_soc_full"
CONF_MIN_SOC_SAFETY = "min_soc_safety"
CONF_MAX_SOC_LIMIT = "max_soc_limit"
CONF_CHARGING_POWER = "charging_power"
CONF_CHARGING_EFFICIENCY = "charging_efficiency"
CONF_PEAK_PRICE_THRESHOLD = "peak_price_threshold"
CONF_CHEAP_PRICE_THRESHOLD = "cheap_price_threshold"
CONF_LOOKAHEAD_HOURS = "lookahead_hours"
CONF_PEAK_PREPARATION_HOURS = "peak_preparation_hours"
CONF_AUTO_CHARGING = "auto_charging"
CONF_TEST_MODE = "test_mode"

# Sensor names
SENSOR_CHARGING_PLAN = "charging_plan"
SENSOR_BATTERY_STATUS = "battery_status"
SENSOR_PRICE_FORECAST = "price_forecast"
SENSOR_NEXT_CHARGING = "next_charging"
SENSOR_DIAGNOSTICS = "diagnostics"

# Service names
SERVICE_FORCE_PLAN_UPDATE = "force_plan_update"
SERVICE_GET_CHARGING_SCHEDULE = "get_charging_schedule"

# Defaults
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
DEFAULT_HISTORY_DAYS = 28
DEFAULT_DISTRIBUTOR = "egd"
DEFAULT_TARIFF = "d57d"
DEFAULT_CIRCUIT_BREAKER = "3x25A"
DEFAULT_PREDICTION_MODE = "adaptive"

# 15-min interval
SLOT_MINUTES = 15
SLOTS_PER_HOUR = 60 // SLOT_MINUTES

# Statistics storage key prefix
STAT_PREFIX = "gw_sc_stat_"

# Savings comparison
CONF_FLAT_PRICE_COMPARE = "flat_price_compare"
DEFAULT_FLAT_PRICE_COMPARE = 4.5  # CZK/kWh - typical Czech flat tariff
