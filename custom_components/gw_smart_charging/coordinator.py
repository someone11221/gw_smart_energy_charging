"""Main coordinator for Smart Battery Charging Controller v3.0.1."""
from datetime import datetime, timedelta
from typing import Optional
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .price_providers.base import PriceProvider
from .price_providers.ote import OTEPriceProvider
from .price_providers.nanogreen import NanogreenPriceProvider
from .battery_controllers.base import BatteryController
from .battery_controllers.goodwe import GoodWeController
from .charging_strategies.intelligent import IntelligentChargingStrategy, ChargingPlan

_LOGGER = logging.getLogger(__name__)

UPDATE_INTERVAL = timedelta(minutes=2)


class SmartChargingCoordinator(DataUpdateCoordinator):
    """Coordinator to manage smart battery charging."""
    
    def __init__(self, hass: HomeAssistant, config: dict):
        """Initialize coordinator."""
        super().__init__(
            hass,
            _LOGGER,
            name="Smart Battery Charging",
            update_interval=UPDATE_INTERVAL,
        )
        
        self.config = config
        self._auto_charging_enabled = config.get("auto_charging", True)
        
        # Initialize price provider
        provider_type = config.get("price_provider", "ote")
        if provider_type == "ote":
            self.price_provider: PriceProvider = OTEPriceProvider(hass, config)
        elif provider_type == "nanogreen":
            self.price_provider = NanogreenPriceProvider(hass, config)
        else:
            _LOGGER.warning(f"Unknown price provider: {provider_type}, using OTE")
            self.price_provider = OTEPriceProvider(hass, config)
        
        # Initialize battery controller
        controller_type = config.get("battery_type", "goodwe")
        if controller_type == "goodwe":
            self.battery_controller: BatteryController = GoodWeController(hass, config)
        else:
            _LOGGER.warning(f"Unknown battery type: {controller_type}, using GoodWe")
            self.battery_controller = GoodWeController(hass, config)
        
        # Initialize charging strategy
        self.strategy = IntelligentChargingStrategy(config)
        
        # Current state
        self.current_plan: Optional[ChargingPlan] = None
        self.last_plan_update: Optional[datetime] = None
        self._charging_active = False
        
        _LOGGER.info(
            f"Initialized SmartChargingCoordinator v3.0.1: "
            f"provider={provider_type}, controller={controller_type}"
        )
    
    async def _async_update_data(self):
        """Update data from all sources."""
        try:
            # Update price data
            await self.price_provider.async_update()
            
            # Update battery status
            await self.battery_controller.async_update()
            
            # Check if we need to recreate plan (every 15 minutes or on first run)
            should_recreate_plan = (
                self.current_plan is None
                or self.last_plan_update is None
                or (datetime.now() - self.last_plan_update).total_seconds() > 900  # 15 min
            )
            
            if should_recreate_plan:
                await self._create_new_plan()
            
            # Decide if we should charge now
            if self._auto_charging_enabled and self.current_plan:
                await self._execute_charging_decision()
            
            # Return data for sensors
            return {
                "battery_status": self.battery_controller._status,
                "current_price": await self.price_provider.get_current_price(),
                "price_forecast": await self.price_provider.get_forecast(24),
                "charging_plan": self.current_plan,
                "charging_active": self._charging_active,
                "auto_enabled": self._auto_charging_enabled,
                "last_update": datetime.now(),
            }
            
        except Exception as e:
            _LOGGER.error(f"Error updating data: {e}", exc_info=True)
            raise UpdateFailed(f"Error updating data: {e}")
    
    async def _create_new_plan(self):
        """Create new charging plan."""
        try:
            battery_status = self.battery_controller._status
            price_forecast = await self.price_provider.get_forecast(48)  # 48 hour lookahead
            
            if not battery_status or not price_forecast:
                _LOGGER.warning("Cannot create plan: missing battery status or price forecast")
                return
            
            # Create new plan
            self.current_plan = await self.strategy.create_charging_plan(
                battery_status=battery_status,
                price_forecast=price_forecast,
                solar_forecast=None  # TODO: Add solar forecast support
            )
            
            self.last_plan_update = datetime.now()
            
            _LOGGER.info(
                f"Created new charging plan: {len(self.current_plan.slots)} slots, "
                f"{self.current_plan.total_kwh:.2f} kWh planned, "
                f"cost {self.current_plan.total_cost:.2f} CZK"
            )
            
            # Log details
            if self.current_plan.slots:
                _LOGGER.debug("Charging slots:")
                for slot in self.current_plan.slots:
                    _LOGGER.debug(
                        f"  {slot.start_time.strftime('%Y-%m-%d %H:%M')} - "
                        f"{slot.end_time.strftime('%H:%M')}: "
                        f"→{slot.target_soc}% @ {slot.price:.2f} CZK/kWh "
                        f"(P{slot.priority}: {slot.reason})"
                    )
            
            if self.current_plan.predicted_peaks:
                _LOGGER.debug("Predicted price peaks:")
                for peak in self.current_plan.predicted_peaks:
                    _LOGGER.debug(
                        f"  {peak.timestamp.strftime('%Y-%m-%d %H:%M')}: "
                        f"{peak.price:.2f} CZK/kWh"
                    )
            
        except Exception as e:
            _LOGGER.error(f"Error creating charging plan: {e}", exc_info=True)
    
    async def _execute_charging_decision(self):
        """Execute charging decision based on plan."""
        if not self.current_plan:
            return
        
        should_charge, reason = self.strategy.should_charge_now(self.current_plan)
        
        # State change detection to avoid unnecessary script calls
        state_changed = should_charge != self._charging_active
        
        if state_changed:
            if should_charge:
                # Start charging
                success = await self.battery_controller.start_charging()
                if success:
                    self._charging_active = True
                    _LOGGER.info(f"✓ STARTED CHARGING: {reason}")
                else:
                    _LOGGER.error("Failed to start charging")
            else:
                # Stop charging
                success = await self.battery_controller.stop_charging()
                if success:
                    self._charging_active = False
                    _LOGGER.info(f"✓ STOPPED CHARGING: {reason}")
                else:
                    _LOGGER.error("Failed to stop charging")
        else:
            # No state change, just log status every 10 minutes
            if int(datetime.now().minute) % 10 == 0:
                status = "CHARGING" if self._charging_active else "NOT CHARGING"
                _LOGGER.debug(f"Status: {status} - {reason}")
    
    async def set_auto_charging(self, enabled: bool):
        """Enable or disable automatic charging."""
        self._auto_charging_enabled = enabled
        _LOGGER.info(f"Auto charging {'ENABLED' if enabled else 'DISABLED'}")
        
        # If disabling, stop any active charging
        if not enabled and self._charging_active:
            await self.battery_controller.stop_charging()
            self._charging_active = False
            _LOGGER.info("Stopped charging due to auto-charging being disabled")
    
    async def force_plan_update(self):
        """Force recreation of charging plan."""
        _LOGGER.info("Forcing plan update...")
        await self._create_new_plan()
        await self.async_request_refresh()
    
    def get_statistics(self) -> dict:
        """Get current statistics."""
        stats = {
            "provider": self.price_provider.name,
            "controller": self.battery_controller.name,
            "auto_enabled": self._auto_charging_enabled,
            "charging_active": self._charging_active,
        }
        
        if self.battery_controller._status:
            stats.update({
                "soc": self.battery_controller._status.soc,
                "battery_power": self.battery_controller._status.power,
                "battery_charging": self.battery_controller._status.charging,
            })
        
        if self.current_plan:
            stats.update({
                "plan_slots": len(self.current_plan.slots),
                "plan_total_kwh": self.current_plan.total_kwh,
                "plan_total_cost": self.current_plan.total_cost,
                "plan_confidence": self.current_plan.confidence,
                "predicted_peaks": len(self.current_plan.predicted_peaks),
            })
        
        return stats
