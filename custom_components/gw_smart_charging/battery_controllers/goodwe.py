"""GoodWe battery controller."""
from datetime import datetime
from typing import Optional
import logging

from .base import BatteryController, BatteryStatus

_LOGGER = logging.getLogger(__name__)


class GoodWeController(BatteryController):
    """Controller for GoodWe battery systems."""
    
    async def async_update(self) -> None:
        """Update battery status from sensors."""
        try:
            # Get SOC sensor
            soc_sensor = self.config.get("soc_sensor", "sensor.battery_state_of_charge")
            soc_state = self.hass.states.get(soc_sensor)
            if not soc_state or soc_state.state in ["unknown", "unavailable"]:
                _LOGGER.warning(f"SOC sensor {soc_sensor} unavailable")
                return
            
            # Get battery power sensor
            power_sensor = self.config.get("battery_power_sensor", "sensor.battery_power")
            power_state = self.hass.states.get(power_sensor)
            if not power_state or power_state.state in ["unknown", "unavailable"]:
                _LOGGER.warning(f"Power sensor {power_sensor} unavailable")
                return
            
            # Parse values
            soc = float(soc_state.state)
            power = float(power_state.state)
            
            # Get capacity from config (default 17 kWh for GoodWe)
            capacity = float(self.config.get("battery_capacity", 17.0))
            
            # Determine charging/discharging state
            # GoodWe: positive power = discharging, negative = charging
            charging = power < -100  # More than 100W charging
            discharging = power > 100  # More than 100W discharging
            
            self._status = BatteryStatus(
                soc=soc,
                power=power,
                capacity=capacity,
                charging=charging,
                discharging=discharging,
                timestamp=datetime.now()
            )
            
            _LOGGER.debug(f"Updated GoodWe status: SOC={soc}%, Power={power}W")
            
        except (ValueError, TypeError) as e:
            _LOGGER.error(f"Error parsing GoodWe sensor values: {e}")
        except Exception as e:
            _LOGGER.error(f"Error updating GoodWe status: {e}", exc_info=True)
    
    async def start_charging(self) -> bool:
        """Start battery charging via script."""
        try:
            script_name = self.config.get("charging_script_on", "script.nabijeni_on")
            
            # Call the charging script
            await self.hass.services.async_call(
                "script",
                script_name.replace("script.", ""),
                {},
                blocking=True
            )
            
            self._charging_active = True
            _LOGGER.info(f"Started GoodWe charging via {script_name}")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Error starting GoodWe charging: {e}", exc_info=True)
            return False
    
    async def stop_charging(self) -> bool:
        """Stop battery charging via script."""
        try:
            script_name = self.config.get("charging_script_off", "script.nabijeni_off")
            
            # Call the stop charging script
            await self.hass.services.async_call(
                "script",
                script_name.replace("script.", ""),
                {},
                blocking=True
            )
            
            self._charging_active = False
            _LOGGER.info(f"Stopped GoodWe charging via {script_name}")
            return True
            
        except Exception as e:
            _LOGGER.error(f"Error stopping GoodWe charging: {e}", exc_info=True)
            return False
    
    async def set_charging_power(self, power_w: int) -> bool:
        """Set charging power limit (if supported by your GoodWe system).
        
        Args:
            power_w: Charging power in watts
            
        Returns:
            True if successful
        """
        # This would need to be implemented based on your specific GoodWe integration
        # For now, just log it
        _LOGGER.info(f"Charging power limit request: {power_w}W (not implemented)")
        return False
    
    async def get_today_charged(self) -> float:
        """Get total energy charged today in kWh."""
        try:
            sensor = self.config.get("today_charge_sensor", "sensor.today_battery_charge")
            state = self.hass.states.get(sensor)
            
            if state and state.state not in ["unknown", "unavailable"]:
                return float(state.state)
            
        except (ValueError, TypeError) as e:
            _LOGGER.debug(f"Error getting today charged: {e}")
        
        return 0.0
    
    async def get_today_discharged(self) -> float:
        """Get total energy discharged today in kWh."""
        try:
            sensor = self.config.get("today_discharge_sensor", "sensor.today_battery_discharge")
            state = self.hass.states.get(sensor)
            
            if state and state.state not in ["unknown", "unavailable"]:
                return float(state.state)
            
        except (ValueError, TypeError) as e:
            _LOGGER.debug(f"Error getting today discharged: {e}")
        
        return 0.0
