"""Consumption predictor v3.2.0 – reads HA Energy Dashboard, adaptive learning.

Sources (priority order):
  1. HA Energy Dashboard entity (energy_dashboard_entity config)
  2. Custom consumption sensor (consumption_sensor config)
  3. Fallback heuristic profile

Modes:
  - "fixed": uses only manual kW values from config
  - "adaptive": learns from history, improves over time
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from dataclasses import dataclass, field
import logging
import statistics

_LOGGER = logging.getLogger(__name__)

SLOTS_PER_DAY = 96
SLOT_DURATION_MIN = 15
SLOT_DURATION_H = 0.25
DEFAULT_HISTORY_DAYS = 28
DEFAULT_FALLBACK_KW = 0.6
DECAY_FACTOR = 0.93  # Exponential decay: recent data weighted higher


@dataclass
class ConsumptionSlot:
    hour: int
    minute: int
    consumption_kwh: float
    confidence: float
    samples: int


@dataclass
class ConsumptionProfile:
    slots: List[ConsumptionSlot]
    total_kwh_24h: float
    avg_power_kw: float
    peak_power_kw: float
    day_of_week: int
    created_at: datetime = field(default_factory=datetime.now)

    def get_consumption_at(self, hour: int, minute: int = 0) -> float:
        idx = hour * 4 + minute // 15
        if 0 <= idx < len(self.slots):
            return self.slots[idx].consumption_kwh
        return DEFAULT_FALLBACK_KW * SLOT_DURATION_H

    def get_power_at(self, hour: int, minute: int = 0) -> float:
        return self.get_consumption_at(hour, minute) / SLOT_DURATION_H

    def get_consumption_range(self, start_hour: int, end_hour: int) -> float:
        return sum(s.consumption_kwh for s in self.slots
                   if start_hour <= s.hour + s.minute / 60 < end_hour)


class ConsumptionPredictor:

    def __init__(self, hass, config: dict):
        self.hass = hass
        self.config = config
        self._profiles: Dict[int, ConsumptionProfile] = {}
        self._last_update: Optional[datetime] = None
        self._raw_history: Dict[int, Dict[int, List[tuple]]] = {}  # dow → slot → [(value, days_ago)]
        self._mode = config.get("prediction_mode", "adaptive")

        # Sensor sources
        self._sensors: List[str] = []
        # Priority 1: HA Energy Dashboard entity
        edash = config.get("energy_dashboard_entity", "")
        if edash:
            self._sensors.append(edash)
        # Priority 2: Custom sensor
        cs = config.get("consumption_sensor", "")
        if cs:
            for s in cs.split(","):
                s = s.strip()
                if s and s not in self._sensors:
                    self._sensors.append(s)
        # Priority 3: auto-detect energy dashboard entities
        self._auto_detect = not self._sensors

        self._history_days = config.get("history_days", DEFAULT_HISTORY_DAYS)

    async def async_update(self) -> None:
        # Fixed mode: only use manual heuristic
        if self._mode == "fixed":
            self._build_fallback_profiles()
            return

        now = datetime.now()
        # Rebuild every 4 hours
        if self._last_update and (now - self._last_update).total_seconds() < 14400:
            return

        # Auto-detect energy dashboard entities if none configured
        if self._auto_detect:
            detected = await self._detect_energy_entities()
            if detected:
                self._sensors = detected
                _LOGGER.info(f"Auto-detected energy entities: {detected}")

        if not self._sensors:
            _LOGGER.debug("No consumption sensors, using fallback")
            self._build_fallback_profiles()
            self._last_update = now
            return

        _LOGGER.info(f"Updating consumption from {len(self._sensors)} sensor(s), mode={self._mode}")
        all_data: Dict[int, Dict[int, List[tuple]]] = {}

        for sensor_id in self._sensors:
            try:
                data = await self._fetch_statistics(sensor_id)
                if not data:
                    data = await self._fetch_state_history(sensor_id)
                if data:
                    self._merge(all_data, data)
            except Exception as e:
                _LOGGER.warning(f"History error for {sensor_id}: {e}")

        if all_data:
            self._raw_history = all_data
            self._build_adaptive_profiles()
            self._last_update = now
            _LOGGER.info("Consumption profiles updated from history")
        else:
            self._build_fallback_profiles()
            self._last_update = now

    async def _detect_energy_entities(self) -> List[str]:
        """Auto-detect entities from HA Energy Dashboard config. Never crashes."""
        candidates = []
        try:
            from homeassistant.components.energy import async_get_manager
            manager = await async_get_manager(self.hass)
            if manager and manager.data:
                prefs = manager.data
                for source in prefs.get("energy_sources", []):
                    if source.get("type") == "grid":
                        for flow in source.get("flow_from", []):
                            eid = flow.get("stat_energy_from")
                            if eid:
                                candidates.append(eid)
        except Exception:
            pass  # energy component not available or not configured

        if not candidates:
            try:
                all_states = self.hass.states.async_all("sensor")
                for state in all_states:
                    unit = state.attributes.get("unit_of_measurement", "")
                    dc = state.attributes.get("device_class", "")
                    sc = state.attributes.get("state_class", "")
                    eid = state.entity_id
                    if (dc == "energy" and sc == "total_increasing" and unit == "kWh"
                            and ("grid" in eid.lower() or "consumption" in eid.lower())):
                        candidates.append(eid)
            except Exception:
                pass

        return candidates[:3]

    async def _fetch_statistics(self, entity_id: str) -> Optional[Dict]:
        """Fetch from HA recorder statistics (hourly)."""
        try:
            from homeassistant.components.recorder.statistics import statistics_during_period
            from homeassistant.components.recorder import get_instance

            now = datetime.now()
            start = now - timedelta(days=self._history_days)
            instance = get_instance(self.hass)

            stats = await instance.async_add_executor_job(
                statistics_during_period, self.hass, start, now,
                {entity_id}, "hour", None, {"change", "mean"})

            if entity_id not in stats or not stats[entity_id]:
                return None

            result: Dict[int, Dict[int, List[tuple]]] = {}
            for entry in stats[entity_id]:
                ts = datetime.fromtimestamp(entry["start"])
                dow = ts.weekday()
                hour = ts.hour
                days_ago = (now - ts).days

                change = entry.get("change")
                mean = entry.get("mean")
                kwh_15 = None

                if change is not None and change >= 0:
                    kwh_15 = float(change) / 4.0
                elif mean is not None and mean >= 0:
                    kw = float(mean)
                    if kw > 100:
                        kw /= 1000.0
                    kwh_15 = kw * SLOT_DURATION_H

                if kwh_15 is not None and kwh_15 >= 0:
                    if dow not in result:
                        result[dow] = {}
                    for q in range(4):
                        si = hour * 4 + q
                        if si not in result[dow]:
                            result[dow][si] = []
                        result[dow][si].append((kwh_15, days_ago))

            return result if result else None
        except Exception as e:
            _LOGGER.debug(f"Statistics fetch failed for {entity_id}: {e}")
            return None

    async def _fetch_state_history(self, entity_id: str) -> Optional[Dict]:
        """Fetch from HA state history (raw changes)."""
        try:
            from homeassistant.components.recorder.history import get_significant_states
            from homeassistant.components.recorder import get_instance

            now = datetime.now()
            start = now - timedelta(days=self._history_days)
            instance = get_instance(self.hass)

            states = await instance.async_add_executor_job(
                get_significant_states, self.hass, start, now, [entity_id])

            if entity_id not in states or not states[entity_id]:
                return None

            state_list = states[entity_id]
            result: Dict[int, Dict[int, List[tuple]]] = {}

            # Detect type
            unit = ""
            for st in state_list[:5]:
                if hasattr(st, 'attributes'):
                    unit = st.attributes.get("unit_of_measurement", "")
                    break
            is_energy = unit in ("kWh", "Wh", "MWh")

            prev_val = prev_ts = None
            for st in state_list:
                try:
                    val = float(st.state)
                    ts = st.last_changed if hasattr(st, 'last_changed') else st.last_updated
                    if isinstance(ts, str):
                        ts = datetime.fromisoformat(ts)
                    days_ago = (now - ts).days

                    if is_energy:
                        if prev_val is not None and prev_ts is not None:
                            delta = val - prev_val
                            dt_h = (ts - prev_ts).total_seconds() / 3600
                            if 0 < delta < 50 and 0 < dt_h < 4:
                                kwh_15 = (delta / dt_h) * SLOT_DURATION_H
                                dow = ts.weekday()
                                si = ts.hour * 4 + ts.minute // 15
                                result.setdefault(dow, {}).setdefault(si, []).append((kwh_15, days_ago))
                        prev_val, prev_ts = val, ts
                    else:
                        kw = val / 1000.0 if abs(val) > 100 else val
                        if kw >= 0:
                            kwh_15 = kw * SLOT_DURATION_H
                            dow = ts.weekday()
                            si = ts.hour * 4 + ts.minute // 15
                            result.setdefault(dow, {}).setdefault(si, []).append((kwh_15, days_ago))
                except (ValueError, TypeError):
                    continue

            return result if result else None
        except Exception as e:
            _LOGGER.debug(f"State history fetch failed for {entity_id}: {e}")
            return None

    def _merge(self, target, source):
        for dow, slots in source.items():
            if dow not in target:
                target[dow] = {}
            for si, vals in slots.items():
                if si not in target[dow]:
                    target[dow][si] = []
                target[dow][si].extend(vals)

    def _build_adaptive_profiles(self):
        """Build profiles with exponential time decay weighting."""
        for dow in range(7):
            slots_data = self._raw_history.get(dow, {})
            slots: List[ConsumptionSlot] = []

            for si in range(SLOTS_PER_DAY):
                hour = si // 4
                minute = (si % 4) * 15
                vals = slots_data.get(si, [])

                if vals and len(vals) >= 2:
                    # Weighted average with exponential decay
                    weighted_sum = 0.0
                    weight_total = 0.0
                    for value, days_ago in vals:
                        w = DECAY_FACTOR ** days_ago
                        weighted_sum += value * w
                        weight_total += w
                    consumption = weighted_sum / weight_total if weight_total > 0 else 0
                    confidence = min(1.0, len(vals) / (self._history_days * 0.5))
                elif vals:
                    consumption = vals[0][0]
                    confidence = 0.3
                else:
                    consumption = self._heuristic_kw(hour) * SLOT_DURATION_H
                    confidence = 0.1

                slots.append(ConsumptionSlot(
                    hour=hour, minute=minute,
                    consumption_kwh=max(0, round(consumption, 4)),
                    confidence=round(confidence, 2), samples=len(vals)))

            total = sum(s.consumption_kwh for s in slots)
            peak = max((s.consumption_kwh / SLOT_DURATION_H for s in slots), default=0)
            self._profiles[dow] = ConsumptionProfile(
                slots=slots, total_kwh_24h=round(total, 2),
                avg_power_kw=round(total / 24, 3), peak_power_kw=round(peak, 3),
                day_of_week=dow)

    def _build_fallback_profiles(self):
        for dow in range(7):
            slots = []
            for si in range(SLOTS_PER_DAY):
                h, m = si // 4, (si % 4) * 15
                c = self._heuristic_kw(h) * SLOT_DURATION_H
                slots.append(ConsumptionSlot(h, m, round(c, 4), 0.1, 0))
            total = sum(s.consumption_kwh for s in slots)
            peak = max(s.consumption_kwh / SLOT_DURATION_H for s in slots)
            self._profiles[dow] = ConsumptionProfile(
                slots=slots, total_kwh_24h=round(total, 2),
                avg_power_kw=round(total / 24, 3), peak_power_kw=round(peak, 3),
                day_of_week=dow)

    def _heuristic_kw(self, hour: int) -> float:
        mo = self.config.get("home_consumption_morning", 1.5)
        ev = self.config.get("home_consumption_evening", 1.8)
        ni = self.config.get("home_consumption_night", 0.4)
        da = self.config.get("home_consumption_kw", 0.8)
        if 6 <= hour <= 9: return mo
        if 17 <= hour <= 21: return ev
        if hour >= 22 or hour <= 5: return ni
        return da

    def get_profile(self, day_of_week: Optional[int] = None) -> ConsumptionProfile:
        if day_of_week is None:
            day_of_week = datetime.now().weekday()
        p = self._profiles.get(day_of_week)
        if not p:
            self._build_fallback_profiles()
            p = self._profiles.get(day_of_week)
        return p

    def predict_next_24h(self) -> List[ConsumptionSlot]:
        now = datetime.now()
        cur_dow = now.weekday()
        nxt_dow = (cur_dow + 1) % 7
        cur_slot = now.hour * 4 + now.minute // 15
        today = self.get_profile(cur_dow)
        tomorrow = self.get_profile(nxt_dow)
        result = today.slots[cur_slot:] + tomorrow.slots[:SLOTS_PER_DAY - len(today.slots[cur_slot:])]
        return result[:SLOTS_PER_DAY]

    def get_predicted_consumption_kw(self, hour: int, minute: int = 0) -> float:
        return self.get_profile().get_power_at(hour, minute)

    def get_diagnostics(self) -> dict:
        return {
            "mode": self._mode,
            "sensors": self._sensors,
            "auto_detect": self._auto_detect,
            "history_days": self._history_days,
            "profiles": len(self._profiles),
            "last_update": self._last_update.isoformat() if self._last_update else None,
        }
