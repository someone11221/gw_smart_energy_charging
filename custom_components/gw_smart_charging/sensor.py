"""Sensors for Smart Battery Charging Controller v3.2.0.

7 sensors (same count as v3.1.0):
  1. Battery SOC - state + power/charging attributes
  2. Battery Power - measurement
  3. Electricity Price - spot + total + HDO/tariff in attributes
  4. Charging Plan - slots + peaks + costs in attributes
  5. Next Charging - time + details
  6. Consumption Forecast - 24h prediction + cost stats in attributes
  7. Diagnostics - version + HDO + statistics summary
"""
from datetime import datetime
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE, UnitOfPower
from .const import DOMAIN, VERSION
from .coordinator import SmartChargingCoordinator
import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass, entry, async_add_entities):
    c = hass.data[DOMAIN][entry.entry_id]
    async_add_entities([
        BatterySOCSensor(c, entry),
        BatteryPowerSensor(c, entry),
        ElectricityPriceSensor(c, entry),
        ChargingPlanSensor(c, entry),
        NextChargingSensor(c, entry),
        ConsumptionForecastSensor(c, entry),
        DiagnosticsSensor(c, entry),
    ])


class _Base(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, c, entry):
        super().__init__(c)
        self._entry = entry

    @property
    def device_info(self):
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Smart Battery Charging",
            "manufacturer": "Custom",
            "model": f"v{VERSION}",
            "sw_version": VERSION,
        }

    def _d(self):
        return self.coordinator.data or {}


class BatterySOCSensor(_Base):
    _attr_name = "Battery SOC"
    _attr_icon = "mdi:battery"
    _attr_native_unit_of_measurement = PERCENTAGE
    _attr_device_class = SensorDeviceClass.BATTERY
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_battery_soc"

    @property
    def native_value(self):
        s = self._d().get("battery_status")
        return round(s.soc, 1) if s else None

    @property
    def extra_state_attributes(self):
        s = self._d().get("battery_status")
        if not s:
            return {}
        return {
            "power_w": s.power,
            "capacity_kwh": s.capacity,
            "charging": s.charging,
            "discharging": s.discharging,
            "is_idle": s.is_idle,
        }


class BatteryPowerSensor(_Base):
    _attr_name = "Battery Power"
    _attr_icon = "mdi:lightning-bolt"
    _attr_native_unit_of_measurement = UnitOfPower.WATT
    _attr_device_class = SensorDeviceClass.POWER
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_battery_power"

    @property
    def native_value(self):
        s = self._d().get("battery_status")
        return round(s.power, 1) if s else None


class ElectricityPriceSensor(_Base):
    """Current spot price + HDO state + tariff info in attributes."""
    _attr_name = "Electricity Price"
    _attr_icon = "mdi:cash-multiple"
    _attr_native_unit_of_measurement = "CZK/kWh"
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_price"

    @property
    def native_value(self):
        p = self._d().get("current_price")
        return round(float(p), 4) if p is not None else None

    @property
    def extra_state_attributes(self):
        d = self._d()
        fc = d.get("price_forecast", {})
        ti = d.get("tariff_info", {})
        hdo = d.get("hdo", {})
        return {
            "min_price": fc.get("min"),
            "max_price": fc.get("max"),
            "avg_price": fc.get("avg"),
            "distributor": ti.get("distributor"),
            "tariff": ti.get("tariff"),
            "tariff_name": ti.get("name"),
            "breaker": ti.get("breaker"),
            "vt_rate": ti.get("total_vt"),
            "nt_rate": ti.get("total_nt"),
            "monthly_fixed_czk": ti.get("monthly_fixed"),
            "current_nt": ti.get("current_nt"),
            "hdo_sensor": hdo.get("sensor"),
            "hdo_available": hdo.get("available"),
            "hdo_state": hdo.get("current"),
        }


class ChargingPlanSensor(_Base):
    """Charging plan with slots, peaks, costs in attributes."""
    _attr_name = "Charging Plan"
    _attr_icon = "mdi:calendar-clock"
    _attr_native_unit_of_measurement = "slots"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_plan"

    @property
    def native_value(self):
        p = self.coordinator.current_plan
        return len(p.slots) if p else 0

    @property
    def extra_state_attributes(self):
        p = self.coordinator.current_plan
        d = self._d()
        st = d.get("statistics", {})
        attrs = {}
        if p:
            attrs.update({
                "slots": [
                    {
                        "start": s.start_time.strftime("%Y-%m-%d %H:%M"),
                        "end": s.end_time.strftime("%H:%M"),
                        "target_soc": s.target_soc,
                        "total_price": round(s.total_price, 4),
                        "priority": s.priority,
                        "reason": s.reason,
                    }
                    for s in p.slots
                ],
                "peaks": [
                    {"time": pk.timestamp.strftime("%Y-%m-%d %H:%M"), "price": round(pk.price, 4)}
                    for pk in p.predicted_peaks
                ],
                "total_cost_czk": round(p.total_cost, 2),
                "total_kwh": round(p.total_kwh, 2),
                "confidence_pct": round(p.confidence * 100, 1),
            })
        # Cost statistics merged here
        today = st.get("today", {})
        week = st.get("week", {})
        month = st.get("month", {})
        attrs.update({
            "cost_today_czk": today.get("cost_czk", 0),
            "cost_week_czk": week.get("total_cost_czk", 0),
            "cost_month_czk": month.get("total_cost_czk", 0),
            "avg_price_month": month.get("avg_price_czk_kwh", 0),
            "nt_share_pct": month.get("nt_share_pct", 0),
        })
        return attrs


class NextChargingSensor(_Base):
    _attr_name = "Next Charging"
    _attr_icon = "mdi:clock-start"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_next"

    @property
    def native_value(self):
        p = self.coordinator.current_plan
        if p and p.slots:
            now = datetime.now()
            future = [s for s in p.slots if s.start_time > now]
            if future:
                ns = min(future, key=lambda s: s.start_time)
                return ns.start_time.strftime("%Y-%m-%d %H:%M")
        return None

    @property
    def extra_state_attributes(self):
        p = self.coordinator.current_plan
        if not p or not p.slots:
            return {}
        now = datetime.now()
        future = [s for s in p.slots if s.start_time > now]
        if not future:
            return {}
        ns = min(future, key=lambda s: s.start_time)
        return {
            "hours_until": round((ns.start_time - now).total_seconds() / 3600, 1),
            "total_price": round(ns.total_price, 4),
            "priority": ns.priority,
            "duration_min": round((ns.end_time - ns.start_time).total_seconds() / 60),
        }


class ConsumptionForecastSensor(_Base):
    """24h consumption forecast + prediction mode info."""
    _attr_name = "Consumption Forecast"
    _attr_icon = "mdi:home-lightning-bolt"
    _attr_native_unit_of_measurement = "kWh"
    _attr_device_class = SensorDeviceClass.ENERGY
    _attr_state_class = SensorStateClass.MEASUREMENT

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_consumption"

    @property
    def native_value(self):
        cf = self._d().get("consumption_forecast", {})
        v = cf.get("total_24h_kwh")
        return round(v, 1) if v is not None else None

    @property
    def extra_state_attributes(self):
        cf = self._d().get("consumption_forecast", {})
        return {
            "avg_kw": cf.get("avg_kw"),
            "peak_kw": cf.get("peak_kw"),
            "source": cf.get("source"),
            "mode": cf.get("mode"),
        }


class DiagnosticsSensor(_Base):
    """Diagnostics with version, HDO, stats summary, errors."""
    _attr_name = "Diagnostics"
    _attr_icon = "mdi:information"
    _attr_entity_category = "diagnostic"

    @property
    def unique_id(self):
        return f"{self._entry.entry_id}_diag"

    @property
    def native_value(self):
        d = self._d()
        if not d:
            return "waiting"
        if d.get("fallback_active"):
            return "fallback"
        if d.get("errors"):
            return f"errors: {len(d['errors'])}"
        if d.get("charging_active"):
            return "charging"
        return "ok"

    @property
    def extra_state_attributes(self):
        d = self._d()
        stats = self.coordinator.get_statistics()
        st = d.get("statistics", {})
        hdo = d.get("hdo", {})
        # Merge everything diagnostic
        attrs = dict(stats)
        attrs["hdo_sensor"] = hdo.get("sensor")
        attrs["hdo_state"] = hdo.get("current")
        attrs["hdo_available"] = hdo.get("available")
        attrs["fallback_active"] = d.get("fallback_active", False)
        attrs["cost_today_czk"] = st.get("today", {}).get("cost_czk", 0)
        attrs["cost_week_czk"] = st.get("week", {}).get("total_cost_czk", 0)
        attrs["cost_month_czk"] = st.get("month", {}).get("total_cost_czk", 0)
        attrs["cost_year_czk"] = st.get("year", {}).get("total_cost_czk", 0)
        attrs["errors"] = d.get("errors", [])
        return attrs
