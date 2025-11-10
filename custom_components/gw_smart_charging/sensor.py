from __future__ import annotations

import logging
from typing import Any, List, Optional
from datetime import datetime

from homeassistant.components.sensor import SensorEntity
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry

from .const import DOMAIN, DEFAULT_NAME
from .coordinator import GWSmartCoordinator

_LOGGER = logging.getLogger(__name__)


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities) -> None:
    """Set up sensors for the config entry."""
    coordinator: GWSmartCoordinator = hass.data[DOMAIN][entry.entry_id]

    entities = [
        GWSmartStatusSensor(coordinator, entry.entry_id),
        GWSmartForecastSensor(coordinator, entry.entry_id),
        GWSmartPriceSensor(coordinator, entry.entry_id),
        GWSmartScheduleSensor(coordinator, entry.entry_id),
        GWSmartSOCSensor(coordinator, entry.entry_id),
        GWSmartDiagnosticsSensor(coordinator, entry.entry_id),  # New diagnostics sensor
        GWSmartBatteryPowerSensor(coordinator, entry.entry_id),  # Real-time battery power
        GWSmartTodayChargeSensor(coordinator, entry.entry_id),  # Today's charge (kWh)
        GWSmartTodayDischargeSensor(coordinator, entry.entry_id),  # Today's discharge (kWh)
        # series sensors for Lovelace plotting (15-min resolution)
        GWSmartSeriesSensor(coordinator, entry.entry_id, "pv"),
        GWSmartSeriesSensor(coordinator, entry.entry_id, "load"),
        GWSmartSeriesSensor(coordinator, entry.entry_id, "battery_charge"),
        GWSmartSeriesSensor(coordinator, entry.entry_id, "battery_discharge"),
        GWSmartSeriesSensor(coordinator, entry.entry_id, "grid_import"),
        GWSmartSeriesSensor(coordinator, entry.entry_id, "soc_forecast"),
    ]

    async_add_entities(entities, True)


class GWSmartStatusSensor(CoordinatorEntity, SensorEntity):
    """Sensor reporting integration status."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Forecast Status"
        self._attr_unique_id = f"{entry_id}_status"

    @property
    def native_value(self) -> str:
        data = self.coordinator.data or {}
        return data.get("status", "unknown")


class GWSmartForecastSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing 15-min PV forecast (kW) plus planned schedule and timestamps."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Forecast"
        self._attr_unique_id = f"{entry_id}_forecast"

    @property
    def native_value(self) -> float:
        """Return a simple numeric state (peak kW) for quick overview."""
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
        # forecast confidence and metadata
        forecast_conf = data.get("forecast_confidence") or {}
        forecast_source = data.get("forecast_source", "")
        forecast_slots = data.get("forecast_slots_count", 0)
        return {
            "forecast_15min": forecast_15min,
            "timestamps": timestamps,
            "schedule_15min": schedule,
            "forecast_confidence": forecast_conf,
            "forecast_source": forecast_source,
            "forecast_slots_count": forecast_slots,
        }


class GWSmartPriceSensor(CoordinatorEntity, SensorEntity):
    """Sensor exposing 15-min prices. State = current 15-min slot price, attribute 'price_15min' = list[96]."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Price"
        self._attr_unique_id = f"{entry_id}_price"
        self._attr_unit_of_measurement = "CZK/kWh"

    @property
    def native_value(self) -> float:
        """Return current 15-min slot price (CZK/kWh) if available."""
        data = self.coordinator.data or {}
        price_15min: List[float] = data.get("price_15min") or []
        if not price_15min:
            return 0.0
        # Calculate current 15-min slot
        now = datetime.now()
        slot = now.hour * 4 + now.minute // 15
        if 0 <= slot < len(price_15min):
            return round(float(price_15min[slot]), 4)
        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        data = self.coordinator.data or {}
        price_15min: List[float] = data.get("price_15min") or [0.0] * 96
        timestamps: List[str] = data.get("timestamps") or []
        return {"price_15min": price_15min, "timestamps": timestamps}


class GWSmartScheduleSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing current charging plan and decision."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Schedule"
        self._attr_unique_id = f"{entry_id}_schedule"

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
        
        return {
            "full_schedule": schedule,
            "current_slot": current_slot,
            "charging_slots_today": charging_slots,
            "current_mode": current_slot.get("mode", "unknown"),
            "should_charge_now": current_slot.get("should_charge", False),
            "current_price": current_slot.get("price_czk_kwh", 0.0),
        }


class GWSmartSOCSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing forecasted battery SOC throughout the day."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} SOC Forecast"
        self._attr_unique_id = f"{entry_id}_soc_forecast"
        self._attr_unit_of_measurement = "%"

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
        
        return {
            "soc_forecast_15min": soc_forecast,
            "timestamps": timestamps,
            "min_soc_pct": round(min_soc, 2),
            "max_soc_pct": round(max_soc, 2),
        }


class GWSmartDiagnosticsSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing integration diagnostics and status information."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Diagnostics"
        self._attr_unique_id = f"{entry_id}_diagnostics"
        self._attr_icon = "mdi:information-outline"

    @property
    def native_value(self) -> str:
        """Return integration status."""
        data = self.coordinator.data or {}
        status = data.get("status", "unknown")
        
        # Get current slot info
        schedule = data.get("schedule") or []
        if schedule:
            now = datetime.now()
            slot = now.hour * 4 + now.minute // 15
            if 0 <= slot < len(schedule):
                current_slot = schedule[slot]
                mode = current_slot.get("mode", "unknown")
                return f"{status} - {mode}"
        
        return status

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
    """Sensor showing current battery power (W, positive=discharging, negative=charging)."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Battery Power"
        self._attr_unique_id = f"{entry_id}_battery_power"
        self._attr_unit_of_measurement = "W"
        self._attr_device_class = "power"
        self._attr_state_class = "measurement"

    @property
    def native_value(self) -> float:
        """Return current battery power in watts."""
        from .const import CONF_BATTERY_POWER_SENSOR
        battery_power_sensor = self.coordinator.config.get(CONF_BATTERY_POWER_SENSOR)
        if battery_power_sensor:
            state = self.coordinator.hass.states.get(battery_power_sensor)
            if state:
                try:
                    # Per requirements: positive when discharging, negative when charging
                    return float(state.state)
                except (ValueError, TypeError):
                    return 0.0
        return 0.0

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Return additional attributes."""
        power_w = self.native_value
        power_kw = power_w / 1000.0
        status = "discharging" if power_w > 0 else "charging" if power_w < 0 else "idle"
        return {
            "power_kw": round(power_kw, 3),
            "status": status,
            "abs_power_w": abs(power_w),
            "abs_power_kw": round(abs(power_kw), 3),
        }


class GWSmartTodayChargeSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing today's total battery charge in kWh."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Today Battery Charge"
        self._attr_unique_id = f"{entry_id}_today_battery_charge"
        self._attr_unit_of_measurement = "kWh"
        self._attr_device_class = "energy"
        self._attr_state_class = "total_increasing"

    @property
    def native_value(self) -> float:
        """Return today's battery charge in kWh."""
        from .const import CONF_TODAY_BATTERY_CHARGE_SENSOR
        charge_sensor = self.coordinator.config.get(CONF_TODAY_BATTERY_CHARGE_SENSOR)
        if charge_sensor:
            state = self.coordinator.hass.states.get(charge_sensor)
            if state:
                try:
                    return round(float(state.state), 3)
                except (ValueError, TypeError):
                    return 0.0
        return 0.0


class GWSmartTodayDischargeSensor(CoordinatorEntity, SensorEntity):
    """Sensor showing today's total battery discharge in kWh."""

    def __init__(self, coordinator: GWSmartCoordinator, entry_id: str) -> None:
        super().__init__(coordinator)
        self._entry_id = entry_id
        self._attr_name = f"{DEFAULT_NAME} Today Battery Discharge"
        self._attr_unique_id = f"{entry_id}_today_battery_discharge"
        self._attr_unit_of_measurement = "kWh"
        self._attr_device_class = "energy"
        self._attr_state_class = "total_increasing"

    @property
    def native_value(self) -> float:
        """Return today's battery discharge in kWh."""
        from .const import CONF_TODAY_BATTERY_DISCHARGE_SENSOR
        discharge_sensor = self.coordinator.config.get(CONF_TODAY_BATTERY_DISCHARGE_SENSOR)
        if discharge_sensor:
            state = self.coordinator.hass.states.get(discharge_sensor)
            if state:
                try:
                    return round(float(state.state), 3)
                except (ValueError, TypeError):
                    return 0.0
        return 0.0
