"""Abstract base class for battery controllers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional
import logging

_LOGGER = logging.getLogger(__name__)


@dataclass
class BatteryStatus:
    """Current battery status."""
    soc: float  # State of charge (0-100%)
    power: float  # Current power (W, positive=discharging, negative=charging)
    capacity: float  # Total capacity (kWh)
    charging: bool  # Is currently charging
    discharging: bool  # Is currently discharging
    timestamp: datetime
    
    @property
    def available_capacity(self) -> float:
        """Get available capacity in kWh."""
        return (self.capacity * self.soc) / 100.0
    
    @property
    def remaining_capacity(self) -> float:
        """Get remaining capacity to full charge in kWh."""
        return (self.capacity * (100 - self.soc)) / 100.0
    
    @property
    def is_idle(self) -> bool:
        """Check if battery is idle (not charging or discharging significantly)."""
        return abs(self.power) < 100  # Less than 100W is considered idle


class BatteryController(ABC):
    """Abstract base class for battery controllers."""
    
    def __init__(self, hass, config: dict):
        """Initialize battery controller."""
        self.hass = hass
        self.config = config
        self._status: Optional[BatteryStatus] = None
        self._charging_active = False
    
    @abstractmethod
    async def async_update(self) -> None:
        """Update battery status."""
        pass
    
    @abstractmethod
    async def start_charging(self) -> bool:
        """Start battery charging.
        
        Returns:
            True if charging started successfully, False otherwise.
        """
        pass
    
    @abstractmethod
    async def stop_charging(self) -> bool:
        """Stop battery charging.
        
        Returns:
            True if charging stopped successfully, False otherwise.
        """
        pass
    
    async def get_status(self) -> Optional[BatteryStatus]:
        """Get current battery status."""
        await self.async_update()
        return self._status
    
    @property
    def name(self) -> str:
        """Get controller name."""
        return self.__class__.__name__.replace("Controller", "")
    
    @property
    def available(self) -> bool:
        """Check if controller is available."""
        return self._status is not None
    
    @property
    def soc(self) -> Optional[float]:
        """Get current state of charge."""
        return self._status.soc if self._status else None
    
    @property
    def is_charging(self) -> bool:
        """Check if battery is currently charging."""
        return self._charging_active and (self._status.charging if self._status else False)
    
    async def can_charge(self, target_kwh: float) -> bool:
        """Check if battery can accept specified charge amount.
        
        Args:
            target_kwh: Amount of energy to charge in kWh
            
        Returns:
            True if battery has capacity for this charge
        """
        if not self._status:
            await self.async_update()
        
        if not self._status:
            return False
        
        return self._status.remaining_capacity >= target_kwh
    
    async def get_charging_time(self, target_soc: float, charging_power: float = 5000) -> float:
        """Estimate time to charge to target SOC.
        
        Args:
            target_soc: Target state of charge (0-100%)
            charging_power: Charging power in watts (default 5000W)
            
        Returns:
            Estimated time in hours
        """
        if not self._status:
            await self.async_update()
        
        if not self._status or target_soc <= self._status.soc:
            return 0.0
        
        kwh_needed = (self._status.capacity * (target_soc - self._status.soc)) / 100.0
        hours_needed = kwh_needed / (charging_power / 1000.0)
        
        return hours_needed
