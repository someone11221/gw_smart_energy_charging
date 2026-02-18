"""OTE (Czech electricity market) price provider with 15-min support."""
from datetime import datetime, timedelta
from typing import Optional, List
import logging

from .base import PriceProvider, PricePoint, PriceForecast

_LOGGER = logging.getLogger(__name__)


def _parse_prices(raw, date, only_from_hour: Optional[int] = None) -> List[PricePoint]:
    """Parse prices from OTE sensor attribute.

    Supports multiple formats:
      - dict:  {"0": 1.23, "1": 2.34, ...}  (hourly)
      - list of dicts:  [{"hour": 0, "price": 1.23}, ...]
      - list of values:  [1.23, 2.34, ...]
      - 15-min format:  [{"hour": 0, "quarter": 0, "price": 1.23}, ...]
      - 15-min index:   96 values where index = hour*4 + quarter
    """
    points: List[PricePoint] = []

    if not raw:
        return points

    # --- DICT format {"0": 1.23, ...} (hourly) ---
    if isinstance(raw, dict):
        for hour_str, price in raw.items():
            try:
                hour = int(hour_str)
                if only_from_hour is not None and hour < only_from_hour:
                    continue
                ts = datetime.combine(date, datetime.min.time()) + timedelta(hours=hour)
                points.append(PricePoint(timestamp=ts, price=float(price), currency="CZK"))
            except (ValueError, TypeError) as e:
                _LOGGER.debug(f"Error parsing dict hour {hour_str}: {e}")
        return points

    # --- LIST format ---
    if isinstance(raw, list):
        # Detect 15-min format (96 entries or dicts with 'quarter' key)
        is_15min = len(raw) > 24 or (
            raw and isinstance(raw[0], dict) and "quarter" in raw[0]
        )

        for idx, item in enumerate(raw):
            try:
                if isinstance(item, dict):
                    hour = int(item.get("hour", item.get("Hour", idx // 4 if is_15min else idx)))
                    quarter = int(item.get("quarter", item.get("Quarter", 0)))
                    price = float(item.get("price", item.get("Price", item.get("value", 0))))
                    minute = quarter * 15 if is_15min else 0
                else:
                    if is_15min:
                        hour = idx // 4
                        minute = (idx % 4) * 15
                    else:
                        hour = idx
                        minute = 0
                    price = float(item)

                if only_from_hour is not None and hour < only_from_hour:
                    continue
                ts = datetime.combine(date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
                points.append(PricePoint(timestamp=ts, price=price, currency="CZK"))
            except (ValueError, TypeError) as e:
                _LOGGER.debug(f"Error parsing list item {idx}: {e}")
        return points

    _LOGGER.warning(f"Unknown price data format: {type(raw)}")
    return points


class OTEPriceProvider(PriceProvider):
    """Provider for OTE (Czech electricity market) spot prices."""

    async def async_update(self) -> None:
        """Update price data from OTE sensor."""
        try:
            sensor_entity = self.config.get("price_sensor")
            if not sensor_entity:
                _LOGGER.error("No price sensor configured for OTE provider")
                return

            state = self.hass.states.get(sensor_entity)
            if not state:
                _LOGGER.warning(f"Price sensor {sensor_entity} not found in HA")
                return

            if state.state in ("unknown", "unavailable"):
                _LOGGER.warning(f"Price sensor {sensor_entity} is {state.state}")
                return

            _LOGGER.debug(f"OTE sensor attributes: {list(state.attributes.keys())}")

            now = datetime.now()
            today_date = now.date()
            tomorrow_date = today_date + timedelta(days=1)

            # Try various attribute names used by different OTE integrations
            today_raw = (
                state.attributes.get("today_hourly_prices")
                or state.attributes.get("today_prices")
                or state.attributes.get("prices_today")
                or state.attributes.get("today")
                # 15-min specific attributes
                or state.attributes.get("today_quarter_prices")
                or state.attributes.get("today_15min_prices")
            )
            tomorrow_raw = (
                state.attributes.get("tomorrow_hourly_prices")
                or state.attributes.get("tomorrow_prices")
                or state.attributes.get("prices_tomorrow")
                or state.attributes.get("tomorrow")
                or state.attributes.get("tomorrow_quarter_prices")
                or state.attributes.get("tomorrow_15min_prices")
            )

            prices: List[PricePoint] = []

            if today_raw is not None:
                today_points = _parse_prices(today_raw, today_date)
                prices.extend(today_points)
                _LOGGER.debug(f"Parsed {len(today_points)} today prices")
            else:
                _LOGGER.warning(
                    f"No today prices found. Available attributes: {list(state.attributes.keys())}"
                )

            if tomorrow_raw is not None:
                tomorrow_points = _parse_prices(tomorrow_raw, tomorrow_date)
                prices.extend(tomorrow_points)
                _LOGGER.debug(f"Parsed {len(tomorrow_points)} tomorrow prices")

            if prices:
                self._forecast = PriceForecast(
                    prices=sorted(prices, key=lambda p: p.timestamp),
                    provider="OTE",
                    fetched_at=datetime.now(),
                )
                _LOGGER.info(f"Updated OTE prices: {len(prices)} data points available")
            else:
                _LOGGER.warning(
                    f"No price data parsed. Sensor state: {state.state}, "
                    f"attributes: {dict(state.attributes)}"
                )

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

        # Try exact 15-min match first
        current_quarter = now.replace(
            minute=(now.minute // 15) * 15, second=0, microsecond=0
        )
        for pp in self._forecast.prices:
            pp_aligned = pp.timestamp.replace(second=0, microsecond=0)
            if pp_aligned == current_quarter:
                return pp.price

        # Fallback: match by hour
        for pp in self._forecast.prices:
            if pp.timestamp.replace(minute=0, second=0, microsecond=0) == current_hour:
                return pp.price

        _LOGGER.warning(f"No price found for current time {now}")
        return None

    async def get_forecast(self, hours: int = 24) -> Optional[PriceForecast]:
        """Get price forecast for next N hours."""
        if not self._forecast:
            await self.async_update()

        if not self._forecast:
            return None

        now = datetime.now()
        current_hour = now.replace(minute=0, second=0, microsecond=0)
        cutoff = now + timedelta(hours=hours)

        filtered_prices = [
            p for p in self._forecast.prices
            if current_hour <= p.timestamp < cutoff
        ]

        if not filtered_prices:
            _LOGGER.warning(
                f"No prices in next {hours}h window – returning all {len(self._forecast.prices)} available"
            )
            if not self._forecast.prices:
                return None
            filtered_prices = self._forecast.prices

        return PriceForecast(
            prices=filtered_prices,
            provider=self._forecast.provider,
            fetched_at=self._forecast.fetched_at,
        )
