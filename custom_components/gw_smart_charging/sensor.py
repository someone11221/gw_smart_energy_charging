"""Sensor platform for Smart Battery Charging Controller v3.0.1."""
from datetime import datetime
from typing import Any, Optional

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass, SensorStateClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import PERCENTAGE, UnitOfEnergy, UnitOfPower

from .const import DOMAIN, VERSION
from .coordinator import SmartChargingCoordinator

import logging

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
):
    """Set up Smart Battery Charging sensors."""
    coordinator: SmartChargingCoordinator = hass.data[DOMAIN][entry.entry_id]
    
    sensors = [
        BatteryStatusSensor(coordinator, entry),
        ChargingPlanSensor(coordinator, entry),
        PriceForecastSensor(coordinator, entry),
        NextChargingSensor(coordinator, entry),
        StatisticsSensor(coordinator, entry),
        DiagnosticsSensor(coordinator, entry),
    ]
    
    async_add_entities(sensors)
    _LOGGER.info(f"Added {len(sensors)} sensors")


class SmartChargingBaseSensor(CoordinatorEntity, SensorEntity):
    """Base sensor for Smart Battery Charging."""
    
    def __init__(self, coordinator: SmartChargingCoordinator, entry: ConfigEntry):
        """Initialize sensor."""
        super().__init__(coordinator)
        self._entry = entry
        self._attr_has_entity_name = True
    
    @property
    def device_info(self):
        """Return device info."""
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Smart Battery Charging Controller",
            "manufacturer": "Martin Rak",
            "model": "Intelligent Charging v3.0.1",
            "sw_version": VERSION,
        }


class BatteryStatusSensor(SmartChargingBaseSensor):
    """Sensor for current battery status."""
    
    _attr_name = "Battery Status"
    _attr_icon = "mdi:battery"
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self._entry.entry_id}_battery_status"
    
    @property
    def native_value(self):
        """Return state of charge."""
        if self.coordinator.data and "battery_status" in self.coordinator.data:
            status = self.coordinator.data["battery_status"]
            return status.soc if status else None
        return None
    
    @property
    def native_unit_of_measurement(self):
        """Return unit of measurement."""
        return PERCENTAGE
    
    @property
    def device_class(self):
        """Return device class."""
        return SensorDeviceClass.BATTERY
    
    @property
    def state_class(self):
        """Return state class."""
        return SensorStateClass.MEASUREMENT
    
    @property
    def extra_state_attributes(self):
        """Return additional attributes."""
        if self.coordinator.data and "battery_status" in self.coordinator.data:
            status = self.coordinator.data["battery_status"]
            if status:
                return {
                    "soc": status.soc,
                    "power": status.power,
                    "capacity": status.capacity,
                    "charging": status.charging,
                    "discharging": status.discharging,
                    "available_capacity_kwh": status.available_capacity,
                    "remaining_capacity_kwh": status.remaining_capacity,
                    "is_idle": status.is_idle,
                    "last_update": status.timestamp.isoformat(),
                }
        return {}


class ChargingPlanSensor(SmartChargingBaseSensor):
    """Sensor for current charging plan."""
    
    _attr_name = "Charging Plan"
    _attr_icon = "mdi:calendar-clock"
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self._entry.entry_id}_charging_plan"
    
    @property
    def native_value(self):
        """Return number of charging slots."""
        if self.coordinator.data and "charging_plan" in self.coordinator.data:
            plan = self.coordinator.data["charging_plan"]
            return len(plan.slots) if plan else 0
        return 0
    
    @property
    def native_unit_of_measurement(self):
        """Return unit of measurement."""
        return "slots"
    
    @property
    def extra_state_attributes(self):
        """Return charging plan details."""
        if self.coordinator.data and "charging_plan" in self.coordinator.data:
            plan = self.coordinator.data["charging_plan"]
            if plan:
                slots = []
                for slot in plan.slots:
                    slots.append({
                        "start": slot.start_time.strftime("%Y-%m-%d %H:%M"),
                        "end": slot.end_time.strftime("%H:%M"),
                        "target_soc": slot.target_soc,
                        "price": round(slot.price, 2),
                        "reason": slot.reason,
                        "priority": slot.priority,
                    })
                
                peaks = []
                for peak in plan.predicted_peaks:
                    peaks.append({
                        "time": peak.timestamp.strftime("%Y-%m-%d %H:%M"),
                        "price": round(peak.price, 2),
                    })
                
                return {
                    "slots": slots,
                    "predicted_peaks": peaks,
                    "total_cost": round(plan.total_cost, 2),
                    "total_kwh": round(plan.total_kwh, 2),
                    "confidence": round(plan.confidence * 100, 1),
                    "created_at": plan.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
        return {}


class PriceForecastSensor(SmartChargingBaseSensor):
    """Sensor for electricity price forecast."""
    
    _attr_name = "Price Forecast"
    _attr_icon = "mdi:cash-multiple"
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self._entry.entry_id}_price_forecast"
    
    @property
    def native_value(self):
        """Return current price."""
        if self.coordinator.data and "current_price" in self.coordinator.data:
            return self.coordinator.data["current_price"]
        return None
    
    @property
    def native_unit_of_measurement(self):
        """Return unit of measurement."""
        return "CZK/kWh"
    
    @property
    def extra_state_attributes(self):
        """Return price forecast data."""
        if self.coordinator.data and "price_forecast" in self.coordinator.data:
            forecast = self.coordinator.data["price_forecast"]
            if forecast:
                prices = []
                for p in forecast.prices[:48]:  # Max 48 hours
                    prices.append({
                        "time": p.timestamp.strftime("%Y-%m-%d %H:%M"),
                        "price": round(p.price, 2),
                    })
                
                cheapest = forecast.get_cheapest_hours(6)
                cheapest_times = [
                    p.timestamp.strftime("%H:%M") for p in cheapest
                ]
                
                peaks = forecast.get_peak_hours(6)
                peak_times = [
                    p.timestamp.strftime("%H:%M") for p in peaks
                ]
                
                return {
                    "prices": prices,
                    "min_price": round(forecast.min_price, 2),
                    "max_price": round(forecast.max_price, 2),
                    "avg_price": round(forecast.avg_price, 2),
                    "volatility": round(forecast.volatility * 100, 1),
                    "cheapest_hours": cheapest_times,
                    "peak_hours": peak_times,
                    "provider": forecast.provider,
                }
        return {}


class NextChargingSensor(SmartChargingBaseSensor):
    """Sensor for next scheduled charging."""
    
    _attr_name = "Next Charging"
    _attr_icon = "mdi:clock-start"
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self._entry.entry_id}_next_charging"
    
    @property
    def native_value(self):
        """Return next charging time."""
        if self.coordinator.data and "charging_plan" in self.coordinator.data:
            plan = self.coordinator.data["charging_plan"]
            if plan and plan.slots:
                now = datetime.now()
                future_slots = [s for s in plan.slots if s.start_time > now]
                if future_slots:
                    next_slot = min(future_slots, key=lambda s: s.start_time)
                    return next_slot.start_time.strftime("%Y-%m-%d %H:%M")
        return "None"
    
    @property
    def extra_state_attributes(self):
        """Return next charging details."""
        if self.coordinator.data and "charging_plan" in self.coordinator.data:
            plan = self.coordinator.data["charging_plan"]
            if plan and plan.slots:
                now = datetime.now()
                future_slots = [s for s in plan.slots if s.start_time > now]
                if future_slots:
                    next_slot = min(future_slots, key=lambda s: s.start_time)
                    hours_until = (next_slot.start_time - now).total_seconds() / 3600
                    
                    return {
                        "start_time": next_slot.start_time.strftime("%Y-%m-%d %H:%M"),
                        "end_time": next_slot.end_time.strftime("%H:%M"),
                        "target_soc": next_slot.target_soc,
                        "price": round(next_slot.price, 2),
                        "reason": next_slot.reason,
                        "priority": next_slot.priority,
                        "hours_until": round(hours_until, 1),
                    }
        return {}


class StatisticsSensor(SmartChargingBaseSensor):
    """Sensor for charging statistics."""
    
    _attr_name = "Statistics"
    _attr_icon = "mdi:chart-line"
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self._entry.entry_id}_statistics"
    
    @property
    def native_value(self):
        """Return confidence score."""
        stats = self.coordinator.get_statistics()
        return round(stats.get("plan_confidence", 0) * 100, 1)
    
    @property
    def native_unit_of_measurement(self):
        """Return unit of measurement."""
        return "%"
    
    @property
    def extra_state_attributes(self):
        """Return statistics."""
        return self.coordinator.get_statistics()


class DiagnosticsSensor(SmartChargingBaseSensor):
    """Sensor for system diagnostics."""
    
    _attr_name = "Diagnostics"
    _attr_icon = "mdi:information"
    _attr_entity_category = "diagnostic"
    
    @property
    def unique_id(self):
        """Return unique ID."""
        return f"{self._entry.entry_id}_diagnostics"
    
    @property
    def native_value(self):
        """Return status."""
        if self.coordinator.data and "charging_active" in self.coordinator.data:
            return "CHARGING" if self.coordinator.data["charging_active"] else "IDLE"
        return "UNKNOWN"
    
    @property
    def extra_state_attributes(self):
        """Return diagnostic information."""
        attrs = {
            "version": VERSION,
            "integration": "Smart Battery Charging Controller v3.0.1",
            "author": "Martin Rak",
        }
        
        if self.coordinator.data:
            attrs.update({
                "last_update": self.coordinator.data.get("last_update", "").isoformat() if self.coordinator.data.get("last_update") else None,
                "auto_enabled": self.coordinator.data.get("auto_enabled", False),
                "charging_active": self.coordinator.data.get("charging_active", False),
            })
        
        stats = self.coordinator.get_statistics()
        attrs.update({
            "provider": stats.get("provider", "unknown"),
            "controller": stats.get("controller", "unknown"),
            "plan_slots": stats.get("plan_slots", 0),
            "predicted_peaks": stats.get("predicted_peaks", 0),
        })
        
        return attrs
