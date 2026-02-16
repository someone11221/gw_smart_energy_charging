"""Abstract base class for electricity price providers."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional


@dataclass
class PricePoint:
    """Represents a single price data point."""
    timestamp: datetime
    price: float  # CZK/kWh
    currency: str = "CZK"
    
    @property
    def hour(self) -> int:
        """Get hour of the day (0-23)."""
        return self.timestamp.hour


@dataclass
class PriceForecast:
    """Forecast of electricity prices."""
    prices: List[PricePoint]
    provider: str
    fetched_at: datetime
    
    @property
    def min_price(self) -> float:
        """Get minimum price in forecast."""
        return min(p.price for p in self.prices)
    
    @property
    def max_price(self) -> float:
        """Get maximum price in forecast."""
        return max(p.price for p in self.prices)
    
    @property
    def avg_price(self) -> float:
        """Get average price in forecast."""
        return sum(p.price for p in self.prices) / len(self.prices)
    
    @property
    def volatility(self) -> float:
        """Calculate price volatility (0-1 scale)."""
        if not self.prices:
            return 0.0
        price_range = self.max_price - self.min_price
        return price_range / self.avg_price if self.avg_price > 0 else 0.0
    
    def get_cheapest_hours(self, count: int = 4) -> List[PricePoint]:
        """Get N cheapest hours from forecast."""
        return sorted(self.prices, key=lambda p: p.price)[:count]
    
    def get_peak_hours(self, count: int = 4) -> List[PricePoint]:
        """Get N most expensive hours from forecast."""
        return sorted(self.prices, key=lambda p: p.price, reverse=True)[:count]


class PriceProvider(ABC):
    """Abstract base class for price providers."""
    
    def __init__(self, hass, config: dict):
        """Initialize price provider."""
        self.hass = hass
        self.config = config
        self._forecast: Optional[PriceForecast] = None
    
    @abstractmethod
    async def async_update(self) -> None:
        """Update price data from provider."""
        pass
    
    @abstractmethod
    async def get_current_price(self) -> Optional[float]:
        """Get current electricity price in CZK/kWh."""
        pass
    
    @abstractmethod
    async def get_forecast(self, hours: int = 24) -> Optional[PriceForecast]:
        """Get price forecast for next N hours."""
        pass
    
    @property
    def name(self) -> str:
        """Get provider name."""
        return self.__class__.__name__.replace("PriceProvider", "")
    
    @property
    def available(self) -> bool:
        """Check if provider is available."""
        return self._forecast is not None
    
    @property
    def last_update(self) -> Optional[datetime]:
        """Get timestamp of last update."""
        return self._forecast.fetched_at if self._forecast else None
