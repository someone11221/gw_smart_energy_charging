"""Intelligent charging strategy v3.2.0 – 15-min intervals, tariff-aware, consumption-predictive."""
from datetime import datetime, timedelta
from typing import List, Optional, Tuple
from dataclasses import dataclass
import logging

from ..price_providers.base import PriceForecast, PricePoint
from ..battery_controllers.base import BatteryStatus
from ..distribution_tariffs import get_distribution_rate_15min, COMMON_REGULATED_PER_KWH
from ..const import SLOT_MINUTES, SLOTS_PER_HOUR

_LOGGER = logging.getLogger(__name__)

SLOT_HOURS = SLOT_MINUTES / 60.0  # 0.25


# ── Legacy compatibility wrapper ──────────────────────────────────

def add_eon_distribution(spot_price_czk: float, hour: int) -> float:
    """Legacy wrapper – kept for dashboard/sensor backward compat."""
    return get_distribution_rate_15min(spot_price_czk, hour, 0, False)


# ── Data classes ──────────────────────────────────────────────────

@dataclass
class ChargingSlot:
    start_time: datetime
    end_time: datetime
    target_soc: float
    price: float           # OTE spot price
    total_price: float     # Price including distribution + regulated
    reason: str
    priority: int          # 1=critical, 2=high, 3=normal, 4=optional


@dataclass
class ChargingPlan:
    slots: List[ChargingSlot]
    predicted_peaks: List[PricePoint]
    total_cost: float
    total_kwh: float
    confidence: float
    created_at: datetime


# ── Strategy ──────────────────────────────────────────────────────

class IntelligentChargingStrategy:
    """
    Smart charging strategy v3.2.0:
    - 15-minute planning granularity
    - Configurable distribution tariffs (EG.D / ČEZ / PRE)
    - Consumption prediction from HA history
    - Peak preparation and opportunistic cheap-hour charging
    """

    def __init__(self, config: dict):
        self.config = config
        self.min_soc_before_peak = config.get("min_soc_before_peak", 80)
        self.target_soc_full = config.get("target_soc_full", 90)
        self.min_soc_safety = config.get("min_soc_safety", 20)
        self.max_soc_limit = config.get("max_soc_limit", 100)
        self.peak_price_threshold = config.get("peak_price_threshold", 0.70)
        self.cheap_price_threshold = config.get("cheap_price_threshold", 0.45)
        self.lookahead_hours = config.get("lookahead_hours", 48)
        self.peak_preparation_hours = config.get("peak_preparation_hours", 4)
        self.battery_capacity_kwh = float(config.get("battery_capacity", 17.0))
        self.charging_power_kw = float(config.get("charging_power", 5.0))
        self.charging_efficiency = config.get("charging_efficiency", 0.95)
        self.home_consumption_kw = config.get("home_consumption_kw", 0.8)

        # Distribution tariff (new in v3.2.0)
        self.distributor = config.get("distributor", "egd")
        self.tariff = config.get("tariff", "d57d")

    # ── Consumption helpers ───────────────────────────────────────

    def _get_consumption_kw(self, dt: datetime, consumption_predictor=None) -> float:
        """Get predicted consumption in kW at a given datetime.

        Uses predictor if available, otherwise falls back to heuristic.
        """
        if consumption_predictor:
            try:
                return consumption_predictor.get_predicted_consumption_kw(
                    dt.hour, dt.minute
                )
            except Exception:
                pass
        return self._heuristic_consumption_kw(dt.hour)

    def _heuristic_consumption_kw(self, hour: int) -> float:
        """Fallback: heuristic consumption by time of day."""
        if 6 <= hour <= 9:
            return self.config.get("home_consumption_morning", 1.5)
        if 17 <= hour <= 21:
            return self.config.get("home_consumption_evening", 1.8)
        if hour >= 22 or hour <= 5:
            return self.config.get("home_consumption_night", 0.4)
        return self.home_consumption_kw

    # ── Price enrichment ──────────────────────────────────────────

    def _enrich_prices(self, forecast: PriceForecast) -> List[dict]:
        """Expand hourly prices to 15-min slots with distribution charges."""
        enriched = []
        for p in forecast.prices:
            is_weekend = p.timestamp.weekday() >= 5
            # Each hourly price point generates 4 quarter-hour slots
            for q in range(SLOTS_PER_HOUR):
                minute = q * SLOT_MINUTES
                ts = p.timestamp.replace(minute=minute, second=0, microsecond=0)
                total = get_distribution_rate_15min(
                    p.price, p.timestamp.hour, minute,
                    is_weekend, self.distributor, self.tariff,
                )
                enriched.append({
                    "point": PricePoint(timestamp=ts, price=p.price),
                    "spot": p.price,
                    "total": total,
                    "hour": ts.hour,
                    "minute": minute,
                    "is_weekend": is_weekend,
                })
        return sorted(enriched, key=lambda x: x["point"].timestamp)

    # ── SOC simulation (15-min steps) ─────────────────────────────

    def _simulate_soc(
        self,
        current_soc: float,
        slots: List[ChargingSlot],
        steps: int = 192,
        consumption_predictor=None,
    ) -> List[float]:
        """Simulate SOC over time in 15-min steps."""
        now = datetime.now().replace(minute=(datetime.now().minute // SLOT_MINUTES) * SLOT_MINUTES,
                                     second=0, microsecond=0)
        soc = current_soc
        timeline = []
        for i in range(steps):
            t = now + timedelta(minutes=i * SLOT_MINUTES)
            is_charging = any(s.start_time <= t < s.end_time for s in slots)
            cons_kw = self._get_consumption_kw(t, consumption_predictor)

            if is_charging:
                net_kw = self.charging_power_kw * self.charging_efficiency - cons_kw
                soc = min(self.max_soc_limit,
                          soc + (net_kw * SLOT_HOURS / self.battery_capacity_kwh * 100))
            else:
                drain = cons_kw * SLOT_HOURS / self.battery_capacity_kwh * 100
                soc = max(0, soc - drain)
            timeline.append(soc)
        return timeline

    # ── Peak & cheap identification ───────────────────────────────

    def _identify_peaks(self, enriched: List[dict]) -> List[dict]:
        """Identify price peaks from total prices."""
        totals = [e["total"] for e in enriched]
        if not totals:
            return []
        avg = sum(totals) / len(totals)
        max_t = max(totals)
        min_t = min(totals)
        threshold = min_t + (max_t - min_t) * self.peak_price_threshold
        threshold = min(threshold, avg * 1.4)

        # Group consecutive above-threshold slots into peak blocks
        peaks = []
        current = None
        for e in enriched:
            if e["total"] >= threshold:
                if current is None:
                    current = e
                else:
                    gap_min = (e["point"].timestamp - current["point"].timestamp).total_seconds() / 60
                    if gap_min <= 30:
                        if e["total"] > current["total"]:
                            current = e
                    else:
                        peaks.append(current)
                        current = e
            else:
                if current:
                    peaks.append(current)
                    current = None
        if current:
            peaks.append(current)

        _LOGGER.info(f"Identified {len(peaks)} peaks (threshold total={threshold:.4f} CZK/kWh)")
        return peaks

    def _identify_cheap_slots(self, enriched: List[dict], current_soc: float) -> List[dict]:
        """Identify cheap 15-min slots for charging."""
        now = datetime.now()
        future = [e for e in enriched if e["point"].timestamp >= now]
        if not future:
            return []

        totals = [e["total"] for e in future]
        min_t, max_t = min(totals), max(totals)
        ratio = self.cheap_price_threshold

        if current_soc < 30:
            ratio = 0.80
        elif current_soc < 50:
            ratio = ratio + 0.20

        threshold = min_t + (max_t - min_t) * ratio
        cheap = [e for e in future if e["total"] <= threshold]
        _LOGGER.info(f"Found {len(cheap)} cheap slots below {threshold:.4f} CZK/kWh (SOC={current_soc}%)")
        return sorted(cheap, key=lambda x: x["total"])

    # ── Helpers ───────────────────────────────────────────────────

    def _slots_needed(self, soc_from: float, soc_to: float) -> int:
        """How many 15-min slots needed to charge from soc_from to soc_to."""
        if soc_to <= soc_from:
            return 0
        kwh = (soc_to - soc_from) / 100 * self.battery_capacity_kwh / self.charging_efficiency
        hours = kwh / self.charging_power_kw
        slots = hours / SLOT_HOURS
        return max(1, int(slots) + (1 if slots % 1 > 0.05 else 0))

    def _ts_key(self, ts: datetime) -> str:
        """Unique key for a 15-min timeslot."""
        aligned = ts.replace(minute=(ts.minute // SLOT_MINUTES) * SLOT_MINUTES,
                             second=0, microsecond=0)
        return aligned.isoformat()[:16]

    # ── Main plan creation ────────────────────────────────────────

    async def create_charging_plan(
        self,
        battery_status: BatteryStatus,
        price_forecast: PriceForecast,
        solar_forecast=None,
        consumption_predictor=None,
    ) -> ChargingPlan:
        if not battery_status or not price_forecast:
            _LOGGER.warning("Missing battery status or price forecast")
            return ChargingPlan([], [], 0, 0, 0, datetime.now())

        current_soc = battery_status.soc
        now = datetime.now()
        charging_slots: List[ChargingSlot] = []
        used_keys: set = set()

        # Expand prices to 15-min slots with distribution
        enriched = self._enrich_prices(price_forecast)
        future_enriched = [e for e in enriched if e["point"].timestamp >= now]

        peaks = self._identify_peaks(future_enriched)
        cheap = self._identify_cheap_slots(enriched, current_soc)

        # ── STEP 1: Peak preparation ────────────────────────────
        for peak in peaks:
            peak_time = peak["point"].timestamp
            hours_until = (peak_time - now).total_seconds() / 3600
            if hours_until < 0 or hours_until > self.lookahead_hours:
                continue

            sim = self._simulate_soc(current_soc, charging_slots,
                                     consumption_predictor=consumption_predictor)
            step_idx = int(hours_until / SLOT_HOURS)
            predicted_soc = sim[min(step_idx, len(sim) - 1)]

            if predicted_soc >= self.min_soc_before_peak:
                _LOGGER.debug(
                    f"Peak at {peak_time}: SOC {predicted_soc:.0f}% >= "
                    f"{self.min_soc_before_peak}% – OK"
                )
                continue

            slots_needed = self._slots_needed(predicted_soc, self.min_soc_before_peak)
            deadline = peak_time - timedelta(minutes=SLOT_MINUTES)
            priority = 1 if hours_until < self.peak_preparation_hours else 2
            max_price = peak["total"] * (0.85 if priority == 1 else 0.70)

            candidates = [
                e for e in future_enriched
                if now <= e["point"].timestamp < deadline
                and e["total"] <= max_price
                and self._ts_key(e["point"].timestamp) not in used_keys
            ]
            candidates.sort(key=lambda x: x["total"])

            for e in candidates[:slots_needed]:
                ts = e["point"].timestamp
                key = self._ts_key(ts)
                used_keys.add(key)
                charging_slots.append(ChargingSlot(
                    start_time=ts,
                    end_time=ts + timedelta(minutes=SLOT_MINUTES),
                    target_soc=self.min_soc_before_peak,
                    price=e["spot"],
                    total_price=e["total"],
                    reason=f"Příprava před peakem {peak_time.strftime('%d.%m %H:%M')} ({e['total']:.4f} CZK/kWh)",
                    priority=priority,
                ))
            _LOGGER.info(
                f"Peak {peak_time}: planned {min(len(candidates), slots_needed)}/{slots_needed} prep slots"
            )

        # ── STEP 2: Emergency – SOC under safety minimum ────────
        if current_soc < self.min_soc_safety + 5:
            slots_needed = self._slots_needed(current_soc, self.min_soc_safety + 15)
            emergency = [
                e for e in future_enriched[:24]  # next 6h at 15-min
                if self._ts_key(e["point"].timestamp) not in used_keys
            ]
            for e in emergency[:slots_needed]:
                ts = e["point"].timestamp
                key = self._ts_key(ts)
                used_keys.add(key)
                charging_slots.append(ChargingSlot(
                    start_time=ts,
                    end_time=ts + timedelta(minutes=SLOT_MINUTES),
                    target_soc=self.min_soc_safety + 15,
                    price=e["spot"],
                    total_price=e["total"],
                    reason=f"EMERGENCY – SOC pod minimem ({e['total']:.4f} CZK/kWh)",
                    priority=1,
                ))

        # ── STEP 3: Opportunistic cheap-slot charging ───────────
        sim_after = self._simulate_soc(current_soc, charging_slots,
                                       consumption_predictor=consumption_predictor)

        max_opp_slots = 32  # Up to 8 hours in 15-min slots
        opp_count = 0

        for e in cheap:
            if opp_count >= max_opp_slots:
                break
            ts = e["point"].timestamp
            key = self._ts_key(ts)
            if key in used_keys or ts < now:
                continue

            test_slots = charging_slots + [ChargingSlot(
                start_time=ts,
                end_time=ts + timedelta(minutes=SLOT_MINUTES),
                target_soc=self.target_soc_full,
                price=e["spot"], total_price=e["total"],
                reason="test", priority=4,
            )]
            sim_test = self._simulate_soc(current_soc, test_slots,
                                          consumption_predictor=consumption_predictor)
            if max(sim_test) < 99:
                used_keys.add(key)
                charging_slots.append(ChargingSlot(
                    start_time=ts,
                    end_time=ts + timedelta(minutes=SLOT_MINUTES),
                    target_soc=self.target_soc_full,
                    price=e["spot"],
                    total_price=e["total"],
                    reason=f"Levná cena {e['total']:.4f} CZK/kWh – oportunistické nabíjení",
                    priority=3,
                ))
                opp_count += 1

        # Sort by time
        charging_slots.sort(key=lambda x: x.start_time)

        # Merge consecutive 15-min slots with same priority into larger blocks
        charging_slots = self._merge_consecutive_slots(charging_slots)

        # ── Statistics ──────────────────────────────────────────
        total_kwh = sum(
            self.charging_power_kw
            * (s.end_time - s.start_time).total_seconds() / 3600
            * self.charging_efficiency
            for s in charging_slots
        )
        total_cost = sum(
            s.total_price * self.charging_power_kw
            * (s.end_time - s.start_time).total_seconds() / 3600
            for s in charging_slots
        )

        confidence = 0.3
        if peaks:
            confidence += 0.3 * min(1.0, len(peaks) / 3)
        if charging_slots:
            confidence += 0.2
        if consumption_predictor and consumption_predictor._last_update:
            confidence += 0.2  # Better data = higher confidence

        peak_points = [p["point"] for p in peaks]

        plan = ChargingPlan(
            slots=charging_slots,
            predicted_peaks=peak_points,
            total_cost=round(total_cost, 2),
            total_kwh=round(total_kwh, 2),
            confidence=round(confidence, 3),
            created_at=now,
        )

        prep_count = sum(1 for s in charging_slots if s.priority <= 2)
        opp_count = sum(1 for s in charging_slots if s.priority >= 3)
        _LOGGER.info(
            f"Plan created: {len(charging_slots)} slots "
            f"({prep_count} prep, {opp_count} opp), "
            f"{total_kwh:.1f} kWh, {total_cost:.2f} CZK"
        )
        return plan

    def _merge_consecutive_slots(self, slots: List[ChargingSlot]) -> List[ChargingSlot]:
        """Merge consecutive 15-min slots with same priority into larger blocks."""
        if not slots:
            return slots

        merged: List[ChargingSlot] = []
        current = slots[0]

        for next_slot in slots[1:]:
            # Merge if consecutive and same priority
            if (next_slot.start_time == current.end_time
                    and next_slot.priority == current.priority):
                current = ChargingSlot(
                    start_time=current.start_time,
                    end_time=next_slot.end_time,
                    target_soc=max(current.target_soc, next_slot.target_soc),
                    price=round((current.price + next_slot.price) / 2, 6),
                    total_price=round((current.total_price + next_slot.total_price) / 2, 6),
                    reason=current.reason,
                    priority=current.priority,
                )
            else:
                merged.append(current)
                current = next_slot
        merged.append(current)
        return merged

    def should_charge_now(self, plan: ChargingPlan, current_time=None) -> Tuple[bool, str]:
        if current_time is None:
            current_time = datetime.now()
        for slot in plan.slots:
            if slot.start_time <= current_time < slot.end_time:
                return True, f"Plánováno: {slot.reason} (P{slot.priority})"
        return False, "Žádné nabíjení v tuto chvíli"
