"""Nanogreen price provider."""
from datetime import datetime, timedelta
from typing import Optional
import logging

from .base import PriceProvider, PricePoint, PriceForecast

_LOGGER = logging.getLogger(__name__)


class NanogreenPriceProvider(PriceProvider):
    """Provider for Nanogreen integration."""
    
    async def async_update(self) -> None:
        """Update price data from Nanogreen sensor."""
        try:
            # Nanogreen uses a binary sensor for cheapest hours
            sensor_entity = self.config.get("nanogreen_sensor", "sensor.is_currently_in_five_cheapest_hours")
            
            state = self.hass.states.get(sensor_entity)
            if not state:
                _LOGGER.warning(f"Nanogreen sensor {sensor_entity} not found")
                return
            
            # Get cheapest hours from attributes
            cheapest_hours = state.attributes.get("cheapest_hours", [])
            all_prices = state.attributes.get("prices", {})
            
            prices = []
            now = datetime.now()
            today_date = now.date()
            
            # Parse prices from Nanogreen format
            for hour_data in all_prices:
                try:
                    hour = hour_data.get("hour", 0)
                    price = hour_data.get("price", 0.0)
                    date_str = hour_data.get("date", str(today_date))
                    
                    # Parse date and create timestamp
                    date = datetime.fromisoformat(date_str).date() if isinstance(date_str, str) else today_date
                    timestamp = datetime.combine(date, datetime.min.time()) + timedelta(hours=hour)
                    
                    if timestamp >= now:  # Only future prices
                        prices.append(PricePoint(
                            timestamp=timestamp,
                            price=float(price),
                            currency="CZK"
                        ))
                except (ValueError, TypeError, KeyError) as e:
                    _LOGGER.debug(f"Error parsing Nanogreen price data: {e}")
            
            if prices:
                self._forecast = PriceForecast(
                    prices=sorted(prices, key=lambda p: p.timestamp),
                    provider="Nanogreen",
                    fetched_at=datetime.now()
                )
                _LOGGER.info(f"Updated Nanogreen prices: {len(prices)} hours available")
            else:
                _LOGGER.warning("No price data available from Nanogreen")
                
        except Exception as e:
            _LOGGER.error(f"Error updating Nanogreen prices: {e}", exc_info=True)
    
    async def get_current_price(self) -> Optional[float]:
        """Get current electricity price."""
        if not self._forecast:
            await self.async_update()
        
        if not self._forecast:
            return None
        
        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        
        for price_point in self._forecast.prices:
            if price_point.timestamp.replace(minute=0, second=0, microsecond=0) == current_hour:
                return price_point.price
        
        return None
    
    async def get_forecast(self, hours: int = 24) -> Optional[PriceForecast]:
        """Get price forecast for next N hours."""
        if not self._forecast:
            await self.async_update()
        
        if not self._forecast:
            return None
        
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
    
    def is_cheapest_hour(self) -> bool:
        """Check if current hour is in cheapest hours."""
        sensor_entity = self.config.get("nanogreen_sensor", "sensor.is_currently_in_five_cheapest_hours")
        state = self.hass.states.get(sensor_entity)
        return state and state.state == "on"
