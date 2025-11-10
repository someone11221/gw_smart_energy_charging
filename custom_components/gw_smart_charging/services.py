from __future__ import annotations

import logging
from typing import Any, Dict, List
from datetime import datetime

from homeassistant.core import HomeAssistant, ServiceCall, ServiceResponse, SupportsResponse
import voluptuous as vol

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

SERVICE_OPTIMIZE = "optimize_now"
SERVICE_APPLY = "apply_schedule_now"
SERVICE_GET_CHARGING_SCHEDULE = "get_charging_schedule"


async def async_setup_services(hass: HomeAssistant) -> None:
    """Register services for the integration."""

    async def _optimize(call: ServiceCall) -> None:
        _LOGGER.info("Service optimize_now called: %s", call.data)
        # placeholder - trigger immediate recalculation
        # Real implementation should call coordinator methods / algorithms.

    async def _apply(call: ServiceCall) -> None:
        _LOGGER.info("Service apply_schedule_now called: %s", call.data)
        # placeholder - apply schedule to switches

    async def _get_charging_schedule(call: ServiceCall) -> ServiceResponse:
        """Get detailed battery charging schedule for automations.
        
        Returns information about:
        - Planned grid charging hours
        - Planned battery discharge hours
        - Planned grid consumption hours (favorable prices)
        - Current activity and state changes
        - Historical consumption optimization data
        """
        _LOGGER.info("Service get_charging_schedule called")
        
        # Get first available coordinator from DOMAIN data
        coordinators = hass.data.get(DOMAIN, {})
        if not coordinators:
            _LOGGER.warning("No coordinators available")
            return {"error": "No integration instance found"}
        
        # Use first coordinator (typically there's only one)
        coordinator = next(iter(coordinators.values()))
        
        # Get schedule data
        data = coordinator.data or {}
        schedule: List[Dict[str, Any]] = data.get("schedule", [])
        
        if not schedule:
            return {"error": "No schedule data available"}
        
        # Get current slot
        now = datetime.now()
        current_slot_index = now.hour * 4 + now.minute // 15
        current_slot = schedule[current_slot_index] if 0 <= current_slot_index < len(schedule) else {}
        
        # Analyze schedule for different activity periods
        grid_charging_periods = []
        battery_discharge_periods = []
        grid_import_periods = []
        solar_charging_periods = []
        
        # Group consecutive slots into periods
        def group_periods(schedule: List[Dict], condition_key: str, condition_value=None):
            """Group consecutive slots matching a condition into periods."""
            periods = []
            current_period = None
            
            for slot in schedule:
                slot_idx = slot.get("slot", 0)
                time_str = slot.get("time", "")
                
                # Check condition
                matches = False
                if condition_value is None:
                    matches = bool(slot.get(condition_key, False))
                else:
                    matches = slot.get(condition_key) == condition_value
                
                if matches:
                    if current_period is None:
                        # Start new period
                        current_period = {
                            "start_time": time_str,
                            "start_slot": slot_idx,
                            "end_time": time_str,
                            "end_slot": slot_idx,
                            "mode": slot.get("mode", "unknown"),
                            "avg_price": slot.get("price_czk_kwh", 0.0),
                            "avg_soc_end": slot.get("soc_pct_end", 0.0),
                            "avg_charge_kw": slot.get("planned_charge_kW", 0.0),
                            "count": 1,
                        }
                    else:
                        # Extend current period
                        current_period["end_time"] = time_str
                        current_period["end_slot"] = slot_idx
                        current_period["avg_price"] += slot.get("price_czk_kwh", 0.0)
                        current_period["avg_soc_end"] += slot.get("soc_pct_end", 0.0)
                        current_period["avg_charge_kw"] += slot.get("planned_charge_kW", 0.0)
                        current_period["count"] += 1
                else:
                    # End current period
                    if current_period:
                        # Calculate averages
                        count = current_period["count"]
                        current_period["avg_price"] = round(current_period["avg_price"] / count, 4)
                        current_period["avg_soc_end"] = round(current_period["avg_soc_end"] / count, 2)
                        current_period["avg_charge_kw"] = round(current_period["avg_charge_kw"] / count, 3)
                        current_period["duration_minutes"] = (current_period["end_slot"] - current_period["start_slot"] + 1) * 15
                        del current_period["count"]
                        periods.append(current_period)
                        current_period = None
            
            # Don't forget last period
            if current_period:
                count = current_period["count"]
                current_period["avg_price"] = round(current_period["avg_price"] / count, 4)
                current_period["avg_soc_end"] = round(current_period["avg_soc_end"] / count, 2)
                current_period["avg_charge_kw"] = round(current_period["avg_charge_kw"] / count, 3)
                current_period["duration_minutes"] = (current_period["end_slot"] - current_period["start_slot"] + 1) * 15
                del current_period["count"]
                periods.append(current_period)
            
            return periods
        
        # Find grid charging periods (grid_charge_cheap, grid_charge_optimal, grid_charge_critical)
        grid_charging_periods = []
        for mode in ["grid_charge_cheap", "grid_charge_optimal", "grid_charge_critical"]:
            periods = group_periods(schedule, "mode", mode)
            grid_charging_periods.extend(periods)
        
        # Find battery discharge periods
        battery_discharge_periods = group_periods(schedule, "mode", "battery_discharge")
        
        # Find solar charging periods
        solar_charging_periods = group_periods(schedule, "mode", "solar_charge")
        
        # Find periods with grid import (when load > PV + battery)
        # These are slots where battery is discharging but not enough to cover load
        for slot in schedule:
            load_kw = slot.get("load_kW", 0.0)
            pv_kw = slot.get("pv_power_kW", 0.0)
            battery_kw = abs(slot.get("planned_charge_kW", 0.0))  # Absolute value
            
            # If load > pv + battery, grid import is expected
            if load_kw > (pv_kw + battery_kw + 0.1):  # 0.1 kW tolerance
                grid_import_periods.append({
                    "time": slot.get("time", ""),
                    "slot": slot.get("slot", 0),
                    "expected_import_kw": round(load_kw - pv_kw - battery_kw, 3),
                    "price_czk_kwh": slot.get("price_czk_kwh", 0.0),
                    "mode": slot.get("mode", "unknown"),
                })
        
        # Get battery and grid metrics
        battery_metrics = data.get("battery_metrics", {})
        grid_metrics = data.get("grid_metrics", {})
        
        # Calculate total energy statistics
        total_grid_charge_kwh = 0.0
        total_solar_charge_kwh = 0.0
        total_battery_discharge_kwh = 0.0
        total_grid_import_kwh = 0.0
        total_cost_czk = 0.0
        
        for slot in schedule:
            charge_kw = slot.get("planned_charge_kW", 0.0)
            price = slot.get("price_czk_kwh", 0.0)
            mode = slot.get("mode", "")
            interval_hours = 0.25  # 15 minutes
            
            if "grid_charge" in mode and charge_kw > 0:
                kwh = charge_kw * interval_hours
                total_grid_charge_kwh += kwh
                total_cost_czk += kwh * price
            elif mode == "solar_charge" and charge_kw > 0:
                total_solar_charge_kwh += charge_kw * interval_hours
            elif mode == "battery_discharge" and charge_kw < 0:
                total_battery_discharge_kwh += abs(charge_kw) * interval_hours
        
        # Prepare response
        response = {
            "current_status": {
                "time": now.strftime("%H:%M"),
                "slot": current_slot_index,
                "mode": current_slot.get("mode", "unknown"),
                "should_charge": current_slot.get("should_charge", False),
                "price_czk_kwh": current_slot.get("price_czk_kwh", 0.0),
                "soc_pct": current_slot.get("soc_pct_end", 0.0),
                "is_critical_hour": current_slot.get("is_critical_hour", False),
            },
            "grid_charging_periods": grid_charging_periods,
            "battery_discharge_periods": battery_discharge_periods,
            "solar_charging_periods": solar_charging_periods,
            "grid_import_slots": grid_import_periods,
            "daily_statistics": {
                "total_grid_charge_kwh": round(total_grid_charge_kwh, 3),
                "total_solar_charge_kwh": round(total_solar_charge_kwh, 3),
                "total_battery_discharge_kwh": round(total_battery_discharge_kwh, 3),
                "estimated_grid_cost_czk": round(total_cost_czk, 2),
                "grid_charging_periods_count": len(grid_charging_periods),
                "solar_charging_periods_count": len(solar_charging_periods),
                "battery_discharge_periods_count": len(battery_discharge_periods),
            },
            "battery_metrics": {
                "current_power_w": battery_metrics.get("battery_power_w", 0.0),
                "current_power_kw": battery_metrics.get("battery_power_kw", 0.0),
                "status": battery_metrics.get("battery_status", "unknown"),
                "soc_pct": battery_metrics.get("soc_pct", 0.0),
                "soc_kwh": battery_metrics.get("soc_kwh", 0.0),
                "today_charge_kwh": battery_metrics.get("today_charge_kwh", 0.0),
                "today_discharge_kwh": battery_metrics.get("today_discharge_kwh", 0.0),
            },
            "grid_metrics": {
                "current_import_w": grid_metrics.get("grid_import_w", 0.0),
                "current_import_kw": grid_metrics.get("grid_import_kw", 0.0),
                "house_load_w": grid_metrics.get("house_load_w", 0.0),
                "house_load_kw": grid_metrics.get("house_load_kw", 0.0),
                "pv_power_w": grid_metrics.get("pv_power_w", 0.0),
                "pv_power_kw": grid_metrics.get("pv_power_kw", 0.0),
            },
            "optimization_info": {
                "ml_prediction_enabled": coordinator.config.get("enable_ml_prediction", False),
                "ml_history_days": len(coordinator._ml_history),
                "battery_capacity_kwh": coordinator.config.get("battery_capacity_kwh", 17.0),
                "target_soc_pct": coordinator.config.get("target_soc_pct", 90.0),
                "always_charge_price": coordinator.config.get("always_charge_price", 1.5),
                "never_charge_price": coordinator.config.get("never_charge_price", 4.0),
            },
            "last_update": data.get("last_update", "never"),
            "automation_active": coordinator.config.get("enable_automation", True),
            "last_script_state": coordinator._last_script_state,
        }
        
        return response

    hass.services.async_register(DOMAIN, SERVICE_OPTIMIZE, _optimize)
    hass.services.async_register(DOMAIN, SERVICE_APPLY, _apply)
    hass.services.async_register(
        DOMAIN, 
        SERVICE_GET_CHARGING_SCHEDULE, 
        _get_charging_schedule,
        supports_response=SupportsResponse.ONLY
    )
