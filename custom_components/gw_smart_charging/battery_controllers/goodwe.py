"""GoodWe battery controller v3.2.0 — graceful degradation."""
from datetime import datetime
from typing import Optional
import logging

from .base import BatteryController, BatteryStatus

_LOGGER = logging.getLogger(__name__)


class GoodWeController(BatteryController):
    """Controller for GoodWe battery systems."""

    async def async_update(self) -> None:
        soc = None
        power = None
        capacity = float(self.config.get("battery_capacity", 17.0))

        # Read SOC
        soc_sensor = self.config.get("soc_sensor", "sensor.battery_state_of_charge")
        soc_state = self.hass.states.get(soc_sensor)
        if soc_state and soc_state.state not in ("unknown", "unavailable", "", "None"):
            try:
                soc = float(soc_state.state)
            except (ValueError, TypeError):
                _LOGGER.debug(f"Cannot parse SOC from {soc_sensor}: {soc_state.state}")
        else:
            _LOGGER.debug(f"SOC sensor {soc_sensor} unavailable (state={soc_state.state if soc_state else 'missing'})")

        # Read power
        power_sensor = self.config.get("battery_power_sensor", "sensor.battery_power")
        power_state = self.hass.states.get(power_sensor)
        if power_state and power_state.state not in ("unknown", "unavailable", "", "None"):
            try:
                power = float(power_state.state)
            except (ValueError, TypeError):
                _LOGGER.debug(f"Cannot parse power from {power_sensor}: {power_state.state}")
        else:
            _LOGGER.debug(f"Power sensor {power_sensor} unavailable")

        # ALWAYS create status — use last known or defaults
        if soc is None and self._status:
            soc = self._status.soc  # keep last known
        if power is None and self._status:
            power = self._status.power
        if soc is None:
            soc = 50.0  # safe default
        if power is None:
            power = 0.0

        charging = power < -100
        discharging = power > 100

        self._status = BatteryStatus(
            soc=soc, power=power, capacity=capacity,
            charging=charging, discharging=discharging,
            timestamp=datetime.now(),
        )

    async def start_charging(self) -> bool:
        try:
            script = self.config.get("charging_script_on", "script.nabijeni_on")
            await self.hass.services.async_call(
                "script", script.replace("script.", ""), {}, blocking=True)
            self._charging_active = True
            _LOGGER.info(f"Charging started: {script}")
            return True
        except Exception as e:
            _LOGGER.error(f"Start charging error: {e}")
            return False

    async def stop_charging(self) -> bool:
        try:
            script = self.config.get("charging_script_off", "script.nabijeni_off")
            await self.hass.services.async_call(
                "script", script.replace("script.", ""), {}, blocking=True)
            self._charging_active = False
            _LOGGER.info(f"Charging stopped: {script}")
            return True
        except Exception as e:
            _LOGGER.error(f"Stop charging error: {e}")
            return False

    async def set_charging_power(self, power_w: int) -> bool:
        _LOGGER.info(f"set_charging_power({power_w}W) not implemented")
        return False

    async def get_today_charged(self) -> float:
        try:
            s = self.hass.states.get(self.config.get("today_charge_sensor", ""))
            if s and s.state not in ("unknown", "unavailable", ""):
                return float(s.state)
        except Exception:
            pass
        return 0.0

    async def get_today_discharged(self) -> float:
        try:
            s = self.hass.states.get(self.config.get("today_discharge_sensor", ""))
            if s and s.state not in ("unknown", "unavailable", ""):
                return float(s.state)
        except Exception:
            pass
        return 0.0
