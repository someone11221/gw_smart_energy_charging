from __future__ import annotations

import logging
from typing import Any, List, Optional, Dict
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity import DeviceInfo

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import GWSmartCoordinator

_LOGGER = logging.getLogger(__name__)


def get_device_info(entry: ConfigEntry) -> DeviceInfo:
    """Return device info for the integration."""
    return DeviceInfo(
        identifiers={(DOMAIN, entry.entry_id)},
        name=DEFAULT_NAME,
        manufacturer="GW Energy Solutions",
        model="Smart Battery Charging Controller",
        sw_version="1.9.0",
        configuration_url="https://github.com/someone11221/gw_smart_energy_charging",
    )


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up sensors for the config entry."""
    coordinator: GWSmartCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        GWSmartForecastSensor(coordinator, entry),
        GWSmartScheduleSensor(coordinator, entry),
        GWSmartSOCSensor(coordinator, entry),
        GWSmartDiagnosticsSensor(coordinator, entry),  # Diagnostics sensor
        GWSmartBatteryPowerSensor(coordinator, entry),  # Real-time battery power
        # Daily statistics and predictions (v1.8.0)
        GWSmartDailyStatisticsSensor(coordinator, entry),  # Daily statistics
        GWSmartPredictionSensor(coordinator, entry),  # ML predictions and forecast
        # Automation support sensors
        GWSmartNextGridChargeSensor(coordinator, entry),  # Next grid charging period
        GWSmartActivityLogSensor(coordinator, entry),  # Activity log and state changes
    ]

    async_add_entities(entities, True)


class GWSmartForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing solar forecast data with charging schedule information."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} Forecast"
        self._attr_unique_id = f"{entry.entry_id}_forecast"
        self._attr_icon = "mdi:solar-power"
        self._attr_unit_of_measurement = "kW"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @property
    def native_value(self) -> float:
        """Return peak solar forecast for quick overview."""
        data = self.coordinator.data or {}
        forecast_15min: List[float] = data.get("forecast_15min") or []
        if not forecast_15min:
            return 0.0
        return round(max(forecast_15min), 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        forecast_15min: List[float] = data.get("forecast_15min") or [0.0] * 96
        schedule: List[dict] = data.get("schedule") or []
        timestamps = data.get("timestamps") or []
        
        # Get current price (15-min slot)
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        price_15min: List[float] = data.get("price_15min") or []
        current_price = price_15min[slot] if 0 <= slot < len(price_15min) else 0.0
        
        # forecast confidence and metadata
        forecast_conf = data.get("forecast_confidence") or {}
        forecast_source = data.get("forecast_source", "")
        forecast_slots = data.get("forecast_slots_count", 0)
        
        # Calculate totals
        total_forecast_kwh = sum(f * 0.25 for f in forecast_15min)  # 15min = 0.25h
        peak_forecast_kw = max(forecast_15min) if forecast_15min else 0.0
        
        return {
            "forecast_15min": forecast_15min,
            "timestamps": timestamps,
            "schedule_15min": schedule,
            "current_price_czk_kwh": round(current_price, 4),
            "price_15min": data.get("price_15min", [0.0] * 96),
            "total_forecast_kwh": round(total_forecast_kwh, 2),
            "peak_forecast_kw": round(peak_forecast_kw, 3),
            "forecast_confidence": forecast_conf,
            "forecast_source": forecast_source,
            "forecast_slots_count": forecast_slots,
        }


class GWSmartScheduleSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing current charging plan and decision."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} Schedule"
        self._attr_unique_id = f"{entry.entry_id}_schedule"
        self._attr_icon = "mdi:calendar-clock"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @property
    def native_value(self) -> str:
        """Return current mode from schedule."""
        data = self.coordinator.data or {}
        schedule: List[dict] = data.get("schedule") or []
        if not schedule:
            return "unknown"
        # Get current 15-min slot
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        if 0 <= slot < len(schedule):
            return schedule[slot].get("mode", "unknown")
        return "unknown"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        schedule: List[dict] = data.get("schedule") or []
        # Get current slot details
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        current_slot = schedule[slot] if 0 <= slot < len(schedule) else {}
        
        # Count charging slots in next 24h
        charging_slots = sum(1 for s in schedule if s.get("should_charge", False))
        
        # Find next charging/discharging periods
        next_charge_time = "none"
        next_discharge_time = "none"
        for i in range(slot + 1, len(schedule)):
            s = schedule[i]
            if next_charge_time == "none" and "grid_charge" in s.get("mode", ""):
                next_charge_time = s.get("time", "unknown")
            if next_discharge_time == "none" and s.get("mode") == "battery_discharge":
                next_discharge_time = s.get("time", "unknown")
            if next_charge_time != "none" and next_discharge_time != "none":
                break
        
        return {
            "full_schedule": schedule,
            "current_slot": current_slot,
            "charging_slots_today": charging_slots,
            "current_mode": current_slot.get("mode", "unknown"),
            "should_charge_now": current_slot.get("should_charge", False),
            "current_price": current_slot.get("price_czk_kwh", 0.0),
            "next_charge_time": next_charge_time,
            "next_discharge_time": next_discharge_time,
        }


class GWSmartSOCSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing forecasted battery SOC throughout the day with series data."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} SOC Forecast"
        self._attr_unique_id = f"{entry.entry_id}_soc_forecast"
        self._attr_unit_of_measurement = "%"
        self._attr_icon = "mdi:battery"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @property
    def native_value(self) -> float:
        """Return forecasted SOC at end of current slot."""
        data = self.coordinator.data or {}
        schedule: List[dict] = data.get("schedule") or []
        if not schedule:
            return 0.0
        # Get current 15-min slot
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        if 0 <= slot < len(schedule):
            return schedule[slot].get("soc_pct_end", 0.0)
        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        schedule: List[dict] = data.get("schedule") or []
        timestamps = data.get("timestamps") or []
        
        # Extract SOC forecast as list
        soc_forecast = [s.get("soc_pct_end", 0.0) for s in schedule]
        
        # Find min/max SOC in forecast
        min_soc = min(soc_forecast) if soc_forecast else 0.0
        max_soc = max(soc_forecast) if soc_forecast else 0.0
        
        # Build series data for charting (same as old series sensors)
        pv_series = [s.get("pv_power_kW", 0.0) for s in schedule]
        load_series = [s.get("load_kW", 0.0) for s in schedule]
        planned_charge = [s.get("planned_charge_kW", 0.0) for s in schedule]
        battery_charge_series = [max(0.0, p) for p in planned_charge]
        battery_discharge_series = [max(0.0, -p) for p in planned_charge]
        
        # Calculate grid import
        grid_import_series = []
        for i in range(len(schedule)):
            pv = pv_series[i] if i < len(pv_series) else 0.0
            load = load_series[i] if i < len(load_series) else 0.0
            batt_charge = battery_charge_series[i] if i < len(battery_charge_series) else 0.0
            batt_discharge = battery_discharge_series[i] if i < len(battery_discharge_series) else 0.0
            
            gi = max(0.0, load - pv)
            if batt_discharge > 0:
                gi = max(0.0, gi - batt_discharge)
            if batt_charge > 0:
                surplus = max(0.0, pv - load)
                extra_charge_from_grid = max(0.0, batt_charge - surplus)
                gi += extra_charge_from_grid
            grid_import_series.append(round(gi, 3))
        
        return {
            "soc_forecast_15min": soc_forecast,
            "timestamps": timestamps,
            "min_soc_pct": round(min_soc, 2),
            "max_soc_pct": round(max_soc, 2),
            # Series data for charting (replaces old series sensors)
            "pv_series_kw": pv_series,
            "load_series_kw": load_series,
            "battery_charge_series_kw": battery_charge_series,
            "battery_discharge_series_kw": battery_discharge_series,
            "grid_import_series_kw": grid_import_series,
        }


class GWSmartDiagnosticsSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing integration diagnostics and status information."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} Diagnostics"
        self._attr_unique_id = f"{entry.entry_id}_diagnostics"
        self._attr_icon = "mdi:information-outline"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @property
    def native_value(self) -> str:
        """Return integration status with current SoC."""
        data = self.coordinator.data or {}
        status = data.get("status", "unknown")
        
        # Get actual current SoC from battery sensor
        battery_metrics = data.get("battery_metrics", {})
        current_soc = battery_metrics.get("soc_pct", 0.0)
        
        # Get current slot info
        schedule = data.get("schedule") or []
        if schedule:
            now = datetime.now()
            slot = now.hour * 4 + now.minute // 15
            if 0 <= slot < len(schedule):
                current_slot = schedule[slot]
                mode = current_slot.get("mode", "unknown")
                return f"{status} - {mode} (SoC: {current_soc:.1f}%)"
        
        return f"{status} (SoC: {current_soc:.1f}%)"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return diagnostics attributes."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule") or []
        
        # Current slot information
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        current_slot = schedule[slot] if 0 <= slot < len(schedule) else {}
        
        # Configuration summary
        from .const import (
            CONF_CHARGING_ON_SCRIPT, CONF_CHARGING_OFF_SCRIPT,
            CONF_ENABLE_AUTOMATION, CONF_FORECAST_SENSOR, CONF_PRICE_SENSOR
        )
        
        # Count different modes
        mode_counts = {}
        charging_slots = 0
        for s in schedule:
            mode = s.get("mode", "unknown")
            mode_counts[mode] = mode_counts.get(mode, 0) + 1
            if s.get("should_charge", False):
                charging_slots += 1
        
        # Find next charging period
        next_charge_slot = None
        for i in range(slot + 1, len(schedule)):
            if schedule[i].get("should_charge", False):
                next_charge_slot = schedule[i]
                break
        
        # Get battery and grid metrics
        battery_metrics = data.get("battery_metrics", {})
        grid_metrics = data.get("grid_metrics", {})
        
        return {
            "last_update": data.get("last_update", "never"),
            "update_interval_minutes": 2,
            "automation_enabled": self.coordinator.config.get(CONF_ENABLE_AUTOMATION, True),
            "charging_on_script": self.coordinator.config.get(CONF_CHARGING_ON_SCRIPT, "not_set"),
            "charging_off_script": self.coordinator.config.get(CONF_CHARGING_OFF_SCRIPT, "not_set"),
            "forecast_sensor": self.coordinator.config.get(CONF_FORECAST_SENSOR, "not_set"),
            "price_sensor": self.coordinator.config.get(CONF_PRICE_SENSOR, "not_set"),
            "current_slot": slot,
            "current_mode": current_slot.get("mode", "unknown"),
            "current_price": current_slot.get("price_czk_kwh", 0.0),
            "current_soc": current_slot.get("soc_pct_end", 0.0),
            "should_charge_now": current_slot.get("should_charge", False),
            "last_script_state": self.coordinator._last_script_state,
            "total_schedule_slots": len(schedule),
            "charging_slots_today": charging_slots,
            "mode_distribution": mode_counts,
            "next_charge_time": next_charge_slot.get("time", "none") if next_charge_slot else "none",
            "next_charge_price": next_charge_slot.get("price_czk_kwh", 0.0) if next_charge_slot else 0.0,
            "forecast_confidence": data.get("forecast_confidence", {}),
            "forecast_source": data.get("forecast_source", "unknown"),
            # Real-time battery metrics
            "battery_power_w": battery_metrics.get("battery_power_w", 0.0),
            "battery_power_kw": battery_metrics.get("battery_power_kw", 0.0),
            "battery_status": battery_metrics.get("battery_status", "unknown"),
            "battery_soc_pct": battery_metrics.get("soc_pct", 0.0),
            "battery_soc_kwh": battery_metrics.get("soc_kwh", 0.0),
            "today_battery_charge_kwh": battery_metrics.get("today_charge_kwh", 0.0),
            "today_battery_discharge_kwh": battery_metrics.get("today_discharge_kwh", 0.0),
            # Real-time grid metrics
            "grid_import_w": grid_metrics.get("grid_import_w", 0.0),
            "grid_import_kw": grid_metrics.get("grid_import_kw", 0.0),
            "house_load_w": grid_metrics.get("house_load_w", 0.0),
            "house_load_kw": grid_metrics.get("house_load_kw", 0.0),
            "pv_power_w": grid_metrics.get("pv_power_w", 0.0),
            "pv_power_kw": grid_metrics.get("pv_power_kw", 0.0),
        }


class GWSmartSeriesSensor(CoordinatorEntity, SensorEntity):
    """Generic series sensor for Lovelace plotting with 15-min resolution.

    series_type in {"pv","load","battery_charge","battery_discharge","grid_import","soc_forecast"}
    Exposes attributes:
      - data_15min: list[96] of floats (kW or % for SOC)
      - timestamps: list[96] of ISO 15-min labels (strings)
    State is current 15-min slot value (float).
    """

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str, series_type: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self.series_type = series_type
        self._attr_name = f"{DEFAULT_NAME} Series {series_type}"
        self._attr_unique_id = f"{entry_id}_series_{series_type}"
        if series_type == "soc_forecast":
            self._attr_unit_of_measurement = "%"
        else:
            self._attr_unit_of_measurement = "kW"

    def _build_series_from_schedule(self, schedule: List[dict]) -> List[float]:
        # Derive series from 15-min schedule data
        pv = []
        load = []
        planned_charge = []
        soc_forecast = []
        
        for s in schedule:
            pv_val = float(s.get("pv_power_kW", 0.0))
            load_val = float(s.get("load_kW", 0.0))
            planned_val = float(s.get("planned_charge_kW", 0.0))  # positive = charge, negative = discharge
            soc_val = float(s.get("soc_pct_end", 0.0))
            
            pv.append(round(pv_val, 3))
            load.append(round(load_val, 3))
            planned_charge.append(round(planned_val, 3))
            soc_forecast.append(round(soc_val, 2))

        battery_charge = [p if p > 0 else 0.0 for p in planned_charge]
        battery_discharge = [-p if p < 0 else 0.0 for p in planned_charge]

        grid_import = []
        for i in range(len(pv)):
            gi = max(0.0, load[i] - pv[i])
            # battery discharge reduces import; battery charge from grid increases import
            if battery_discharge[i] > 0:
                gi = max(0.0, gi - battery_discharge[i])
            if battery_charge[i] > 0:
                surplus = max(0.0, pv[i] - load[i])
                extra_charge_from_grid = max(0.0, battery_charge[i] - surplus)
                gi += extra_charge_from_grid
            grid_import.append(round(gi, 3))

        mapping = {
            "pv": pv,
            "load": load,
            "battery_charge": battery_charge,
            "battery_discharge": battery_discharge,
            "grid_import": grid_import,
            "soc_forecast": soc_forecast,
        }
        return mapping.get(self.series_type, [0.0] * 96)

    def _build_series_from_fallback(self, coordinator_data: dict) -> List[float]:
        # fallback: use 15min data if schedule absent
        forecast = coordinator_data.get("forecast_15min") or [0.0] * 96
        load = coordinator_data.get("load_15min") or [0.0] * 96
        battery_charge = [0.0] * 96
        battery_discharge = [0.0] * 96
        grid_import = [max(0.0, load[i] - forecast[i]) for i in range(96)]
        soc_forecast = [50.0] * 96  # flat 50% if no data
        
        mapping = {
            "pv": forecast,
            "load": load,
            "battery_charge": battery_charge,
            "battery_discharge": battery_discharge,
            "grid_import": grid_import,
            "soc_forecast": soc_forecast,
        }
        return mapping.get(self.series_type, [0.0] * 96)

    def _build_timestamps(self, coordinator_data: dict) -> List[str]:
        # Prefer coordinator timestamps if provided; otherwise build simple "HH:MM" labels for 15-min
        timestamps = coordinator_data.get("timestamps")
        if isinstance(timestamps, list) and len(timestamps) >= 96:
            return timestamps[:96]
        # Build 15-min labels
        labels = []
        for h in range(24):
            for m in [0, 15, 30, 45]:
                labels.append(f"{h:02d}:{m:02d}")
        return labels

    @property
    def native_value(self) -> float:
        """Return value for current 15-min slot."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule")
        if schedule:
            arr = self._build_series_from_schedule(schedule)
        else:
            arr = self._build_series_from_fallback(data)
        
        # Get current 15-min slot
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        if 0 <= slot < len(arr):
            return round(float(arr[slot]), 3 if self.series_type != "soc_forecast" else 2)
        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        schedule = data.get("schedule")
        if schedule:
            arr = self._build_series_from_schedule(schedule)
        else:
            arr = self._build_series_from_fallback(data)
        timestamps = self._build_timestamps(data)
        return {"data_15min": arr, "timestamps": timestamps}


class GWSmartBatteryPowerSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing current battery power and today's charge/discharge totals."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} Battery Power"
        self._attr_unique_id = f"{entry.entry_id}_battery_power"
        self._attr_unit_of_measurement = "W"
        self._attr_device_class = "power"
        self._attr_state_class = "measurement"
        self._attr_icon = "mdi:battery-charging"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @property
    def native_value(self) -> float:
        """Return current battery power in watts."""
        data = self.coordinator.data or {}
        battery_metrics = data.get("battery_metrics", {})
        return battery_metrics.get("battery_power_w", 0.0)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes including today's totals."""
        data = self.coordinator.data or {}
        battery_metrics = data.get("battery_metrics", {})
        
        power_w = battery_metrics.get("battery_power_w", 0.0)
        power_kw = battery_metrics.get("battery_power_kw", 0.0)
        status = battery_metrics.get("battery_status", "idle")
        soc_pct = battery_metrics.get("soc_pct", 0.0)
        soc_kwh = battery_metrics.get("soc_kwh", 0.0)
        today_charge = battery_metrics.get("today_charge_kwh", 0.0)
        today_discharge = battery_metrics.get("today_discharge_kwh", 0.0)
        
        return {
            "power_kw": round(power_kw, 3),
            "status": status,
            "abs_power_w": abs(power_w),
            "abs_power_kw": round(abs(power_kw), 3),
            "current_soc_pct": round(soc_pct, 1),
            "current_soc_kwh": round(soc_kwh, 2),
            "today_charge_kwh": round(today_charge, 3),
            "today_discharge_kwh": round(today_discharge, 3),
            "today_net_kwh": round(today_charge - today_discharge, 3),
        }


class GWSmartNextGridChargeSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing next planned grid charging and battery discharge periods."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} Next Charge"
        self._attr_unique_id = f"{entry.entry_id}_next_charge"
        self._attr_icon = "mdi:battery-clock"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @property
    def native_value(self) -> str:
        """Return time of next grid charging period."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule", [])
        
        if not schedule:
            return "none"
        
        # Get current slot
        now = datetime.now()
        current_slot = now.hour * 4 + now.minute // 15
        
        # Find next grid charging slot
        for i in range(current_slot, len(schedule)):
            slot = schedule[i]
            mode = slot.get("mode", "")
            if "grid_charge" in mode:
                return slot.get("time", "unknown")
        
        # Check from beginning if not found
        for i in range(0, current_slot):
            slot = schedule[i]
            mode = slot.get("mode", "")
            if "grid_charge" in mode:
                return f"{slot.get('time', 'unknown')} (tomorrow)"
        
        return "none"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed attributes for next charging and discharge periods."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule", [])
        
        if not schedule:
            return {}
        
        now = datetime.now()
        current_slot = now.hour * 4 + now.minute // 15
        
        # Find all grid charging periods today
        grid_charge_periods = []
        discharge_periods = []
        current_period = None
        discharge_period = None
        
        for slot in schedule:
            mode = slot.get("mode", "")
            slot_idx = slot.get("slot", 0)
            
            # Process grid charging periods
            if "grid_charge" in mode:
                if current_period is None:
                    current_period = {
                        "start_time": slot.get("time", ""),
                        "start_slot": slot_idx,
                        "end_time": slot.get("time", ""),
                        "end_slot": slot_idx,
                        "mode": mode,
                        "avg_price": slot.get("price_czk_kwh", 0.0),
                        "count": 1,
                    }
                elif slot_idx == current_period["end_slot"] + 1:
                    # Consecutive slot
                    current_period["end_time"] = slot.get("time", "")
                    current_period["end_slot"] = slot_idx
                    current_period["avg_price"] += slot.get("price_czk_kwh", 0.0)
                    current_period["count"] += 1
                else:
                    # New period
                    current_period["avg_price"] /= current_period["count"]
                    current_period["duration_minutes"] = (current_period["end_slot"] - current_period["start_slot"] + 1) * 15
                    grid_charge_periods.append(current_period)
                    current_period = {
                        "start_time": slot.get("time", ""),
                        "start_slot": slot_idx,
                        "end_time": slot.get("time", ""),
                        "end_slot": slot_idx,
                        "mode": mode,
                        "avg_price": slot.get("price_czk_kwh", 0.0),
                        "count": 1,
                    }
            else:
                if current_period:
                    current_period["avg_price"] /= current_period["count"]
                    current_period["duration_minutes"] = (current_period["end_slot"] - current_period["start_slot"] + 1) * 15
                    grid_charge_periods.append(current_period)
                    current_period = None
            
            # Process battery discharge periods
            if mode == "battery_discharge":
                if discharge_period is None:
                    discharge_period = {
                        "start_time": slot.get("time", ""),
                        "start_slot": slot_idx,
                        "end_time": slot.get("time", ""),
                        "end_slot": slot_idx,
                        "avg_discharge_kw": abs(slot.get("planned_charge_kW", 0.0)),
                        "count": 1,
                    }
                elif slot_idx == discharge_period["end_slot"] + 1:
                    discharge_period["end_time"] = slot.get("time", "")
                    discharge_period["end_slot"] = slot_idx
                    discharge_period["avg_discharge_kw"] += abs(slot.get("planned_charge_kW", 0.0))
                    discharge_period["count"] += 1
                else:
                    discharge_period["avg_discharge_kw"] /= discharge_period["count"]
                    discharge_period["duration_minutes"] = (discharge_period["end_slot"] - discharge_period["start_slot"] + 1) * 15
                    discharge_periods.append(discharge_period)
                    discharge_period = {
                        "start_time": slot.get("time", ""),
                        "start_slot": slot_idx,
                        "end_time": slot.get("time", ""),
                        "end_slot": slot_idx,
                        "avg_discharge_kw": abs(slot.get("planned_charge_kW", 0.0)),
                        "count": 1,
                    }
            else:
                if discharge_period:
                    discharge_period["avg_discharge_kw"] /= discharge_period["count"]
                    discharge_period["duration_minutes"] = (discharge_period["end_slot"] - discharge_period["start_slot"] + 1) * 15
                    discharge_periods.append(discharge_period)
                    discharge_period = None
        
        # Don't forget last periods
        if current_period:
            current_period["avg_price"] /= current_period["count"]
            current_period["duration_minutes"] = (current_period["end_slot"] - current_period["start_slot"] + 1) * 15
            grid_charge_periods.append(current_period)
        
        if discharge_period:
            discharge_period["avg_discharge_kw"] /= discharge_period["count"]
            discharge_period["duration_minutes"] = (discharge_period["end_slot"] - discharge_period["start_slot"] + 1) * 15
            discharge_periods.append(discharge_period)
        
        # Find next periods
        next_charge_period = None
        next_discharge_period = None
        
        for period in grid_charge_periods:
            if period["start_slot"] >= current_slot:
                next_charge_period = period
                break
        
        for period in discharge_periods:
            if period["start_slot"] >= current_slot:
                next_discharge_period = period
                break
        
        # If not found, use first periods (tomorrow)
        if not next_charge_period and grid_charge_periods:
            next_charge_period = grid_charge_periods[0]
            next_charge_period["is_tomorrow"] = True
        
        if not next_discharge_period and discharge_periods:
            next_discharge_period = discharge_periods[0]
            next_discharge_period["is_tomorrow"] = True
        
        attrs = {
            "all_charge_periods_today": grid_charge_periods,
            "total_charge_periods": len(grid_charge_periods),
            "all_discharge_periods_today": discharge_periods,
            "total_discharge_periods": len(discharge_periods),
        }
        
        if next_charge_period:
            attrs.update({
                "next_charge_start_time": next_charge_period["start_time"],
                "next_charge_end_time": next_charge_period["end_time"],
                "next_charge_duration_minutes": next_charge_period["duration_minutes"],
                "next_charge_avg_price": round(next_charge_period["avg_price"], 4),
                "next_charge_mode": next_charge_period["mode"],
                "next_charge_is_tomorrow": next_charge_period.get("is_tomorrow", False),
            })
        
        if next_discharge_period:
            attrs.update({
                "next_discharge_start_time": next_discharge_period["start_time"],
                "next_discharge_end_time": next_discharge_period["end_time"],
                "next_discharge_duration_minutes": next_discharge_period["duration_minutes"],
                "next_discharge_avg_kw": round(next_discharge_period["avg_discharge_kw"], 3),
                "next_discharge_is_tomorrow": next_discharge_period.get("is_tomorrow", False),
            })
        
        return attrs


class GWSmartActivityLogSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing activity log and state changes for automations."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} Activity Log"
        self._attr_unique_id = f"{entry.entry_id}_activity_log"
        self._attr_icon = "mdi:history"
        self._activity_log: List[Dict[str, Any]] = []
        self._last_mode = None
        self._last_should_charge = None

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @property
    def native_value(self) -> str:
        """Return current activity status."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule", [])
        
        if not schedule:
            return "no_data"
        
        now = datetime.now()
        current_slot = now.hour * 4 + now.minute // 15
        
        if 0 <= current_slot < len(schedule):
            current_slot_data = schedule[current_slot]
            mode = current_slot_data.get("mode", "unknown")
            should_charge = current_slot_data.get("should_charge", False)
            
            # Track state changes
            if mode != self._last_mode or should_charge != self._last_should_charge:
                self._add_activity_log(mode, should_charge, current_slot_data)
                self._last_mode = mode
                self._last_should_charge = should_charge
            
            # Return human-readable status
            if should_charge:
                return f"charging ({mode})"
            elif mode == "battery_discharge":
                return "discharging"
            elif mode == "solar_charge":
                return "solar_charging"
            else:
                return mode
        
        return "unknown"

    def _add_activity_log(self, mode: str, should_charge: bool, slot_data: Dict[str, Any]) -> None:
        """Add an entry to the activity log."""
        now = datetime.now()
        
        entry = {
            "timestamp": now.isoformat(),
            "time": now.strftime("%H:%M"),
            "mode": mode,
            "should_charge": should_charge,
            "price_czk_kwh": slot_data.get("price_czk_kwh", 0.0),
            "soc_pct": slot_data.get("soc_pct_end", 0.0),
            "is_critical_hour": slot_data.get("is_critical_hour", False),
        }
        
        self._activity_log.append(entry)
        
        # Keep only last 100 entries
        if len(self._activity_log) > 100:
            self._activity_log = self._activity_log[-100:]

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return activity log and statistics."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule", [])
        battery_metrics = data.get("battery_metrics", {})
        
        # Count mode changes today
        mode_changes = {}
        for i in range(len(schedule) - 1):
            current_mode = schedule[i].get("mode", "unknown")
            next_mode = schedule[i + 1].get("mode", "unknown")
            if current_mode != next_mode:
                transition = f"{current_mode} -> {next_mode}"
                mode_changes[transition] = mode_changes.get(transition, 0) + 1
        
        # Get recent activity (last 10 entries)
        recent_activity = self._activity_log[-10:] if self._activity_log else []
        
        return {
            "activity_log": self._activity_log,
            "recent_activity": recent_activity,
            "total_log_entries": len(self._activity_log),
            "mode_transitions_today": mode_changes,
            "last_update": data.get("last_update", "never"),
            "battery_status": battery_metrics.get("battery_status", "unknown"),
            "current_soc_pct": battery_metrics.get("soc_pct", 0.0),
            "automation_active": self.coordinator.config.get("enable_automation", True),
            "last_script_state": self.coordinator._last_script_state,
        }


class GWSmartDailyStatisticsSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing daily statistics for charging optimization."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} Daily Statistics"
        self._attr_unique_id = f"{entry.entry_id}_daily_statistics"
        self._attr_icon = "mdi:chart-bar"
        self._attr_unit_of_measurement = "kWh"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @property
    def native_value(self) -> float:
        """Return total planned energy for today."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule", [])
        
        if not schedule:
            return 0.0
        
        # Calculate total grid charge planned
        total_grid_charge = 0.0
        interval_hours = 0.25  # 15 minutes
        
        for slot in schedule:
            charge_kw = slot.get("planned_charge_kW", 0.0)
            mode = slot.get("mode", "")
            if "grid_charge" in mode and charge_kw > 0:
                total_grid_charge += charge_kw * interval_hours
        
        return round(total_grid_charge, 3)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return detailed daily statistics."""
        data = self.coordinator.data or {}
        schedule = data.get("schedule", [])
        battery_metrics = data.get("battery_metrics", {})
        
        if not schedule:
            return {}
        
        interval_hours = 0.25  # 15 minutes
        
        # Calculate statistics
        total_grid_charge_kwh = 0.0
        total_solar_charge_kwh = 0.0
        total_battery_discharge_kwh = 0.0
        total_grid_cost_czk = 0.0
        
        grid_charge_slots = 0
        solar_charge_slots = 0
        discharge_slots = 0
        
        for slot in schedule:
            charge_kw = slot.get("planned_charge_kW", 0.0)
            price = slot.get("price_czk_kwh", 0.0)
            mode = slot.get("mode", "")
            
            if "grid_charge" in mode and charge_kw > 0:
                kwh = charge_kw * interval_hours
                total_grid_charge_kwh += kwh
                total_grid_cost_czk += kwh * price
                grid_charge_slots += 1
            elif mode == "solar_charge" and charge_kw > 0:
                total_solar_charge_kwh += charge_kw * interval_hours
                solar_charge_slots += 1
            elif mode == "battery_discharge" and charge_kw < 0:
                total_battery_discharge_kwh += abs(charge_kw) * interval_hours
                discharge_slots += 1
        
        # Get actual today's data from sensors
        today_charge = battery_metrics.get("today_charge_kwh", 0.0)
        today_discharge = battery_metrics.get("today_discharge_kwh", 0.0)
        
        return {
            "planned_grid_charge_kwh": round(total_grid_charge_kwh, 3),
            "planned_solar_charge_kwh": round(total_solar_charge_kwh, 3),
            "planned_battery_discharge_kwh": round(total_battery_discharge_kwh, 3),
            "estimated_grid_cost_czk": round(total_grid_cost_czk, 2),
            "grid_charge_slots": grid_charge_slots,
            "solar_charge_slots": solar_charge_slots,
            "discharge_slots": discharge_slots,
            "actual_today_charge_kwh": today_charge,
            "actual_today_discharge_kwh": today_discharge,
            "charge_efficiency_pct": round((today_charge / total_grid_charge_kwh * 100) if total_grid_charge_kwh > 0 else 0, 1),
            "savings_vs_flat_rate": round(self._calculate_savings(schedule, total_grid_cost_czk), 2),
        }
    
    def _calculate_savings(self, schedule: List[dict], optimized_cost: float) -> float:
        """Calculate savings compared to flat-rate charging."""
        if not schedule:
            return 0.0
        
        # Calculate what it would cost at average price
        prices = [s.get("price_czk_kwh", 0.0) for s in schedule if s.get("price_czk_kwh", 0.0) > 0]
        if not prices:
            return 0.0
        
        avg_price = sum(prices) / len(prices)
        
        # Calculate total grid charge
        interval_hours = 0.25
        total_kwh = 0.0
        for slot in schedule:
            charge_kw = slot.get("planned_charge_kW", 0.0)
            mode = slot.get("mode", "")
            if "grid_charge" in mode and charge_kw > 0:
                total_kwh += charge_kw * interval_hours
        
        flat_rate_cost = total_kwh * avg_price
        return flat_rate_cost - optimized_cost


class GWSmartPredictionSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing ML predictions and forecast confidence."""

    def __init__(self, coordinator: GWSmartCoordinator, entry: ConfigEntry) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._attr_name = f"{DEFAULT_NAME} Prediction"
        self._attr_unique_id = f"{entry.entry_id}_prediction"
        self._attr_icon = "mdi:crystal-ball"

    @property
    def device_info(self) -> DeviceInfo:
        """Return device info."""
        return get_device_info(self._entry)

    @property
    def native_value(self) -> str:
        """Return prediction status."""
        from .const import CONF_ENABLE_ML_PREDICTION, DEFAULT_ENABLE_ML_PREDICTION
        
        ml_enabled = self.coordinator.config.get(CONF_ENABLE_ML_PREDICTION, DEFAULT_ENABLE_ML_PREDICTION)
        ml_history_days = len(self.coordinator._ml_history)
        
        if not ml_enabled:
            return "disabled"
        elif ml_history_days == 0:
            return "learning"
        elif ml_history_days < 7:
            return "low_confidence"
        elif ml_history_days < 14:
            return "medium_confidence"
        else:
            return "high_confidence"

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return prediction details."""
        from .const import CONF_ENABLE_ML_PREDICTION, DEFAULT_ENABLE_ML_PREDICTION
        from datetime import datetime
        
        data = self.coordinator.data or {}
        
        ml_enabled = self.coordinator.config.get(CONF_ENABLE_ML_PREDICTION, DEFAULT_ENABLE_ML_PREDICTION)
        ml_history_days = len(self.coordinator._ml_history)
        
        # Get forecast confidence
        forecast_conf = data.get("forecast_confidence", {})
        forecast_source = data.get("forecast_source", "unknown")
        forecast_slots = data.get("forecast_slots_count", 0)
        
        # Calculate prediction quality score (0-100)
        quality_score = 0
        if ml_enabled and ml_history_days > 0:
            # ML quality: 0-50 points based on history days
            ml_quality = min(50, (ml_history_days / 30.0) * 50)
            quality_score += ml_quality
        
        # Forecast quality: 0-50 points
        forecast_quality = forecast_conf.get("score", 0.0) * 50
        quality_score += forecast_quality
        
        # Get today's date info
        today = datetime.now()
        is_weekend = today.weekday() >= 5
        
        return {
            "ml_enabled": ml_enabled,
            "ml_history_days": ml_history_days,
            "ml_confidence": "high" if ml_history_days >= 14 else "medium" if ml_history_days >= 7 else "low" if ml_history_days > 0 else "none",
            "forecast_confidence_score": round(forecast_conf.get("score", 0.0), 3),
            "forecast_confidence_reason": forecast_conf.get("reason", ""),
            "forecast_source": forecast_source,
            "forecast_data_points": forecast_slots,
            "prediction_quality_score": round(quality_score, 1),
            "is_weekend": is_weekend,
            "day_of_week": today.strftime("%A"),
            "total_confidence": "high" if quality_score >= 70 else "medium" if quality_score >= 40 else "low",
        }

