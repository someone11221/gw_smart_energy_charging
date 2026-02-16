"""OTE (Czech electricity market) price provider."""
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from .base import PriceProvider, PricePoint, PriceForecast

_LOGGER = logging.getLogger(__name__)


class OTEPriceProvider(PriceProvider):
    """Provider for OTE (Czech electricity market) spot prices."""
    
    async def async_update(self) -> None:
        """Update price data from OTE sensor."""
        try:
            # Get sensor entity
            sensor_entity = self.config.get("price_sensor")
            if not sensor_entity:
                _LOGGER.error("No price sensor configured for OTE provider")
                return
            
            state = self.hass.states.get(sensor_entity)
            if not state:
                _LOGGER.warning(f"Price sensor {sensor_entity} not found")
                return
            
            # Parse today's and tomorrow's prices from attributes
            today_prices = state.attributes.get("today_hourly_prices", {})
            tomorrow_prices = state.attributes.get("tomorrow_hourly_prices", {})
            
            prices = []
            now = datetime.now()
            today_date = now.date()
            
            # Add today's prices (only future hours)
            for hour_str, price in today_prices.items():
                try:
                    hour = int(hour_str)
                    if hour >= now.hour:  # Only future hours
                        timestamp = datetime.combine(today_date, datetime.min.time()) + timedelta(hours=hour)
                        prices.append(PricePoint(
                            timestamp=timestamp,
                            price=float(price),
                            currency="CZK"
                        ))
                except (ValueError, TypeError) as e:
                    _LOGGER.debug(f"Error parsing hour {hour_str}: {e}")
            
            # Add tomorrow's prices
            tomorrow_date = today_date + timedelta(days=1)
            for hour_str, price in tomorrow_prices.items():
                try:
                    hour = int(hour_str)
                    timestamp = datetime.combine(tomorrow_date, datetime.min.time()) + timedelta(hours=hour)
                    prices.append(PricePoint(
                        timestamp=timestamp,
                        price=float(price),
                        currency="CZK"
                    ))
                except (ValueError, TypeError) as e:
                    _LOGGER.debug(f"Error parsing hour {hour_str}: {e}")
            
            if prices:
                self._forecast = PriceForecast(
                    prices=sorted(prices, key=lambda p: p.timestamp),
                    provider="OTE",
                    fetched_at=datetime.now()
                )
                _LOGGER.info(f"Updated OTE prices: {len(prices)} hours available")
            else:
                _LOGGER.warning("No price data available from OTE sensor")
                
        except Exception as e:
            _LOGGER.error(f"Error updating OTE prices: {e}", exc_info=True)
    
    async def get_current_price(self) -> Optional[float]:
        """Get current electricity price."""
        if not self._forecast:
            await self.async_update()
        
        if not self._forecast:
            return None
        
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        # Find price for current hour
        for price_point in self._forecast.prices:
            if price_point.timestamp.replace(minute=0, second=0, microsecond=0) == current_hour:
                return price_point.price
        
        _LOGGER.warning("No price found for current hour")
        return None
    
    async def get_forecast(self, hours: int = 24) -> Optional[PriceForecast]:
        """Get price forecast for next N hours."""
        if not self._forecast:
            await self.async_update()
        
        if not self._forecast:
            return None
        
        # Filter to requested number of hours
        now = datetime.now()
        cutoff = now + timedelta(hours=hours)
        
        filtered_prices = [
            p for p in self._forecast.prices
            if now <= p.timestamp < cutoff
        ]
        
        if not filtered_prices:
            return None
        
        return PriceForecast(
            prices=filtered_prices,
            provider=self._forecast.provider,
            fetched_at=self._forecast.fetched_at
        )
