"""Intelligent charging strategy with peak price prediction and optimization."""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

from ..price_providers.base import PriceForecast, PricePoint
from ..battery_controllers.base import BatteryStatus

_LOGGER = logging.getLogger(__name__)


@dataclass
class ChargingSlot:
    """Represents a planned charging slot."""
    start_time: datetime
    end_time: datetime
    target_soc: float
    price: float
    reason: str  # Why this slot was chosen
    priority: int  # 1=critical, 2=high, 3=normal, 4=opportunistic


@dataclass
class ChargingPlan:
    """Complete charging plan with slots and predictions."""
    slots: List[ChargingSlot]
    predicted_peaks: List[PricePoint]
    total_cost: float
    total_kwh: float
    confidence: float  # 0-1, how confident we are in this plan
    created_at: datetime


class IntelligentChargingStrategy:
    """
    Advanced charging strategy that:
    1. Predicts price peaks in the next 24-48 hours
    2. Ensures battery has enough capacity before peaks
    3. Charges during cheapest periods
    4. Optimizes for minimum cost while maintaining availability
    """
    
    def __init__(self, config: dict):
        """Initialize strategy with configuration."""
        self.config = config
        
        # Strategy parameters
        self.min_soc_before_peak = config.get("min_soc_before_peak", 80)  # % SOC before peak
        self.target_soc_full = config.get("target_soc_full", 95)  # % Full charge target
        self.min_soc_safety = config.get("min_soc_safety", 20)  # % Never go below
        self.max_soc_limit = config.get("max_soc_limit", 100)  # % Never exceed
        
        # Price thresholds
        self.peak_price_threshold = config.get("peak_price_threshold", 0.75)  # Top 25% = peak
        self.cheap_price_threshold = config.get("cheap_price_threshold", 0.35)  # Bottom 35% = cheap
        
        # Timing parameters
        self.lookahead_hours = config.get("lookahead_hours", 24)
        self.peak_preparation_hours = config.get("peak_preparation_hours", 4)  # Hours before peak to be ready
        
        # Battery parameters
        self.battery_capacity_kwh = config.get("battery_capacity", 17.0)
        self.charging_power_kw = config.get("charging_power", 5.0)  # kW
        self.charging_efficiency = config.get("charging_efficiency", 0.95)  # 95% efficient
    
    def _identify_peaks(self, forecast: PriceForecast) -> List[PricePoint]:
        """Identify price peaks in forecast.
        
        A peak is defined as:
        - Price in top 25% of forecast range
        - OR price > 1.5x average
        - Consecutive high-price hours are merged into single peak
        """
        if not forecast or not forecast.prices:
            return []
        
        avg_price = forecast.avg_price
        price_range = forecast.max_price - forecast.min_price
        peak_threshold = forecast.min_price + (price_range * self.peak_price_threshold)
        
        # Alternative threshold: 1.5x average
        alt_threshold = avg_price * 1.5
        
        # Use the lower threshold (more aggressive peak detection)
        threshold = min(peak_threshold, alt_threshold)
        
        peaks = []
        current_peak = None
        
        for price_point in sorted(forecast.prices, key=lambda p: p.timestamp):
            if price_point.price >= threshold:
                if current_peak is None:
                    # Start new peak
                    current_peak = price_point
                else:
                    # Extend current peak if consecutive
                    time_diff = (price_point.timestamp - current_peak.timestamp).total_seconds() / 3600
                    if time_diff <= 2:  # Within 2 hours = same peak
                        # Update to highest price in peak
                        if price_point.price > current_peak.price:
                            current_peak = price_point
                    else:
                        # Gap > 2 hours, save current peak and start new
                        peaks.append(current_peak)
                        current_peak = price_point
            else:
                # End of peak
                if current_peak:
                    peaks.append(current_peak)
                    current_peak = None
        
        # Don't forget last peak
        if current_peak:
            peaks.append(current_peak)
        
        _LOGGER.info(f"Identified {len(peaks)} price peaks with threshold {threshold:.2f} CZK/kWh")
        for peak in peaks:
            _LOGGER.debug(f"  Peak at {peak.timestamp}: {peak.price:.2f} CZK/kWh")
        
        return peaks
    
    def _identify_cheap_slots(self, forecast: PriceForecast, count: int = None) -> List[PricePoint]:
        """Identify cheapest charging slots.
        
        Args:
            forecast: Price forecast
            count: Number of slots to return (default: auto-calculate based on need)
        """
        if not forecast or not forecast.prices:
            return []
        
        # Sort by price
        sorted_prices = sorted(forecast.prices, key=lambda p: p.price)
        
        # Calculate cheap threshold (bottom 35% of range)
        price_range = forecast.max_price - forecast.min_price
        cheap_threshold = forecast.min_price + (price_range * self.cheap_price_threshold)
        
        # Get all slots below threshold
        cheap_slots = [p for p in sorted_prices if p.price <= cheap_threshold]
        
        # If count specified, limit to that
        if count:
            cheap_slots = cheap_slots[:count]
        
        _LOGGER.debug(f"Found {len(cheap_slots)} cheap slots below {cheap_threshold:.2f} CZK/kWh")
        
        return cheap_slots
    
    def _calculate_required_charge(
        self, 
        current_soc: float, 
        target_soc: float
    ) -> float:
        """Calculate kWh needed to reach target SOC."""
        soc_diff = max(0, target_soc - current_soc)
        kwh_needed = (soc_diff / 100.0) * self.battery_capacity_kwh
        return kwh_needed / self.charging_efficiency  # Account for charging losses
    
    def _calculate_charging_slots_needed(self, kwh_needed: float) -> int:
        """Calculate how many 1-hour slots needed for charging."""
        if kwh_needed <= 0:
            return 0
        
        hours_needed = kwh_needed / self.charging_power_kw
        return int(hours_needed) + (1 if hours_needed % 1 > 0.1 else 0)
    
    async def create_charging_plan(
        self,
        battery_status: BatteryStatus,
        price_forecast: PriceForecast,
        solar_forecast: Optional[dict] = None
    ) -> ChargingPlan:
        """Create intelligent charging plan.
        
        Strategy:
        1. Identify price peaks in next 24-48 hours
        2. Ensure battery reaches min_soc_before_peak before each peak
        3. Schedule charging during cheapest periods
        4. Aim for full charge (target_soc_full) if very cheap prices available
        5. Never let SOC drop below min_soc_safety
        
        Args:
            battery_status: Current battery status
            price_forecast: Price forecast for planning period
            solar_forecast: Optional solar production forecast
        
        Returns:
            ChargingPlan with scheduled slots
        """
        if not battery_status or not price_forecast:
            _LOGGER.warning("Missing battery status or price forecast")
            return ChargingPlan([], [], 0, 0, 0, datetime.now())
        
        current_soc = battery_status.soc
        current_time = datetime.now()
        
        # Step 1: Identify peaks
        peaks = self._identify_peaks(price_forecast)
        
        # Step 2: Identify cheap slots
        cheap_slots = self._identify_cheap_slots(price_forecast)
        
        charging_slots = []
        
        # Step 3: Plan charging before each peak
        for peak in peaks:
            # How long until peak?
            hours_until_peak = (peak.timestamp - current_time).total_seconds() / 3600
            
            if hours_until_peak < self.peak_preparation_hours:
                # Peak is very soon, urgent charging if below target
                if current_soc < self.min_soc_before_peak:
                    kwh_needed = self._calculate_required_charge(current_soc, self.min_soc_before_peak)
                    slots_needed = self._calculate_charging_slots_needed(kwh_needed)
                    
                    # Find cheapest slots before peak
                    available_slots = [
                        s for s in cheap_slots 
                        if current_time <= s.timestamp < peak.timestamp
                    ]
                    
                    if available_slots:
                        # Use cheapest available slots
                        selected = sorted(available_slots, key=lambda x: x.price)[:slots_needed]
                        
                        for slot in selected:
                            charging_slots.append(ChargingSlot(
                                start_time=slot.timestamp,
                                end_time=slot.timestamp + timedelta(hours=1),
                                target_soc=self.min_soc_before_peak,
                                price=slot.price,
                                reason=f"Urgent prep for peak at {peak.timestamp.strftime('%H:%M')}",
                                priority=1  # Critical
                            ))
            
            elif hours_until_peak < self.lookahead_hours:
                # Peak is within lookahead window, plan preparation
                # Target to be at min_soc_before_peak at least 2 hours before peak
                prep_deadline = peak.timestamp - timedelta(hours=2)
                
                if current_soc < self.min_soc_before_peak:
                    kwh_needed = self._calculate_required_charge(current_soc, self.min_soc_before_peak)
                    slots_needed = self._calculate_charging_slots_needed(kwh_needed)
                    
                    # Find cheapest slots before deadline
                    available_slots = [
                        s for s in cheap_slots 
                        if current_time <= s.timestamp < prep_deadline
                    ]
                    
                    if available_slots:
                        selected = sorted(available_slots, key=lambda x: x.price)[:slots_needed]
                        
                        for slot in selected:
                            charging_slots.append(ChargingSlot(
                                start_time=slot.timestamp,
                                end_time=slot.timestamp + timedelta(hours=1),
                                target_soc=self.min_soc_before_peak,
                                price=slot.price,
                                reason=f"Prep for peak at {peak.timestamp.strftime('%H:%M')}",
                                priority=2  # High
                            ))
        
        # Step 4: Opportunistic full charging during very cheap periods
        if current_soc < self.target_soc_full:
            # Find ultra-cheap slots (bottom 20%)
            ultra_cheap = sorted(cheap_slots, key=lambda x: x.price)[:int(len(cheap_slots) * 0.2)]
            
            kwh_to_full = self._calculate_required_charge(current_soc, self.target_soc_full)
            slots_for_full = self._calculate_charging_slots_needed(kwh_to_full)
            
            # Filter out already-used slots
            used_times = {slot.start_time for slot in charging_slots}
            available_ultra_cheap = [
                s for s in ultra_cheap 
                if s.timestamp not in used_times and s.timestamp >= current_time
            ]
            
            if len(available_ultra_cheap) >= slots_for_full:
                # We have enough ultra-cheap slots for full charge!
                selected = available_ultra_cheap[:slots_for_full]
                
                for slot in selected:
                    charging_slots.append(ChargingSlot(
                        start_time=slot.timestamp,
                        end_time=slot.timestamp + timedelta(hours=1),
                        target_soc=self.target_soc_full,
                        price=slot.price,
                        reason="Opportunistic full charge at ultra-low price",
                        priority=3  # Normal
                    ))
        
        # Step 5: Safety net - ensure minimum SOC
        if current_soc < self.min_soc_safety:
            # Emergency charging needed NOW
            kwh_needed = self._calculate_required_charge(current_soc, self.min_soc_safety + 10)
            
            # Find next available slot
            next_slots = sorted(
                [s for s in price_forecast.prices if s.timestamp >= current_time],
                key=lambda x: x.timestamp
            )[:2]  # Next 2 hours
            
            for slot in next_slots:
                charging_slots.append(ChargingSlot(
                    start_time=slot.timestamp,
                    end_time=slot.timestamp + timedelta(hours=1),
                    target_soc=self.min_soc_safety + 10,
                    price=slot.price,
                    reason="EMERGENCY - SOC below safety minimum",
                    priority=1  # Critical
                ))
        
        # Sort slots by time and remove duplicates
        charging_slots = sorted(
            list({slot.start_time: slot for slot in charging_slots}.values()),
            key=lambda x: x.start_time
        )
        
        # Calculate total cost and kWh
        total_kwh = sum(
            self._calculate_required_charge(current_soc, slot.target_soc) 
            for slot in charging_slots
        )
        total_cost = sum(slot.price * (self.charging_power_kw) for slot in charging_slots)
        
        # Calculate confidence (based on forecast quality and peak detection)
        confidence = min(1.0, len(peaks) / 3.0) * 0.7  # Base confidence
        if len(charging_slots) > 0:
            confidence += 0.3  # Bonus if we have a plan
        
        plan = ChargingPlan(
            slots=charging_slots,
            predicted_peaks=peaks,
            total_cost=total_cost,
            total_kwh=total_kwh,
            confidence=confidence,
            created_at=current_time
        )
        
        _LOGGER.info(
            f"Created charging plan: {len(charging_slots)} slots, "
            f"{total_kwh:.2f} kWh, {total_cost:.2f} CZK, "
            f"confidence {confidence:.0%}"
        )
        
        return plan
    
    def should_charge_now(
        self,
        plan: ChargingPlan,
        current_time: Optional[datetime] = None
    ) -> Tuple[bool, str]:
        """Determine if charging should be active right now.
        
        Args:
            plan: Current charging plan
            current_time: Current time (default: now)
        
        Returns:
            (should_charge, reason) tuple
        """
        if current_time is None:
            current_time = datetime.now()
        
        # Check if we're in any scheduled charging slot
        for slot in plan.slots:
            if slot.start_time <= current_time < slot.end_time:
                return True, f"Scheduled: {slot.reason} (Priority {slot.priority})"
        
        return False, "No charging scheduled at this time"
