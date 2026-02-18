"""Historical statistics tracker for energy costs and consumption.

Tracks and persists:
- Energy consumed per hour/day/month (kWh)
- Cost per hour/day/month (CZK) including spot + distribution
- Average price paid
- Charging vs grid consumption breakdown
- Peak/off-peak consumption split

Data persisted via HA storage helper (survives restarts).
"""
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field, asdict
import json
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.storage import Store

_LOGGER = logging.getLogger(__name__)
STORAGE_KEY = "gw_smart_charging_statistics"
STORAGE_VERSION = 2


@dataclass
class HourStat:
    """Statistics for one hour."""
    hour: int
    kwh_charged: float = 0.0     # kWh charged from grid into battery
    kwh_consumed: float = 0.0    # kWh total household consumption
    cost_czk: float = 0.0        # Total cost CZK
    spot_price_avg: float = 0.0  # Avg spot price during this hour
    total_price_avg: float = 0.0 # Avg total price (spot+dist)
    is_nt: bool = False          # Was this NT period
    samples: int = 0


@dataclass
class DayStat:
    """Statistics for one day."""
    date: str                     # "YYYY-MM-DD"
    hours: Dict[int, dict] = field(default_factory=dict)
    total_kwh_charged: float = 0.0
    total_kwh_consumed: float = 0.0
    total_cost_czk: float = 0.0
    avg_spot_price: float = 0.0
    avg_total_price: float = 0.0
    nt_kwh: float = 0.0
    vt_kwh: float = 0.0
    peak_kwh: float = 0.0        # kWh during peak hours
    cheapest_hour: int = 0
    most_expensive_hour: int = 0
    charging_sessions: int = 0

    def recalculate(self):
        """Recalculate totals from hourly data."""
        if not self.hours:
            return
        self.total_kwh_charged = sum(h.get("kwh_charged", 0) for h in self.hours.values())
        self.total_kwh_consumed = sum(h.get("kwh_consumed", 0) for h in self.hours.values())
        self.total_cost_czk = sum(h.get("cost_czk", 0) for h in self.hours.values())
        self.nt_kwh = sum(h.get("kwh_consumed", 0) for h in self.hours.values() if h.get("is_nt"))
        self.vt_kwh = sum(h.get("kwh_consumed", 0) for h in self.hours.values() if not h.get("is_nt"))

        prices = [(int(k), h.get("total_price_avg", 0)) for k, h in self.hours.items() if h.get("samples", 0) > 0]
        if prices:
            self.cheapest_hour = min(prices, key=lambda x: x[1])[0]
            self.most_expensive_hour = max(prices, key=lambda x: x[1])[0]

        total_samples = sum(h.get("samples", 0) for h in self.hours.values())
        if total_samples > 0:
            self.avg_spot_price = sum(h.get("spot_price_avg", 0) * h.get("samples", 0) for h in self.hours.values()) / total_samples
            self.avg_total_price = sum(h.get("total_price_avg", 0) * h.get("samples", 0) for h in self.hours.values()) / total_samples


class StatisticsTracker:
    """Tracks and persists energy cost statistics."""

    def __init__(self, hass: HomeAssistant, entry_id: str):
        self.hass = hass
        self._store = Store(hass, STORAGE_VERSION, f"{STORAGE_KEY}_{entry_id}")
        self._days: Dict[str, DayStat] = {}
        self._loaded = False
        self._dirty = False

    async def async_load(self):
        """Load persisted statistics."""
        data = await self._store.async_load()
        if data and isinstance(data, dict):
            for date_str, day_data in data.get("days", {}).items():
                ds = DayStat(date=date_str)
                ds.hours = day_data.get("hours", {})
                ds.total_kwh_charged = day_data.get("total_kwh_charged", 0)
                ds.total_kwh_consumed = day_data.get("total_kwh_consumed", 0)
                ds.total_cost_czk = day_data.get("total_cost_czk", 0)
                ds.avg_spot_price = day_data.get("avg_spot_price", 0)
                ds.avg_total_price = day_data.get("avg_total_price", 0)
                ds.nt_kwh = day_data.get("nt_kwh", 0)
                ds.vt_kwh = day_data.get("vt_kwh", 0)
                ds.charging_sessions = day_data.get("charging_sessions", 0)
                self._days[date_str] = ds
            _LOGGER.info(f"Loaded statistics: {len(self._days)} days")
        self._loaded = True

    async def async_save(self):
        """Persist statistics to disk."""
        if not self._dirty:
            return
        data = {"days": {}}
        # Keep last 400 days (>1 year)
        cutoff = (datetime.now() - timedelta(days=400)).strftime("%Y-%m-%d")
        for d_str, ds in sorted(self._days.items()):
            if d_str >= cutoff:
                data["days"][d_str] = {
                    "hours": ds.hours,
                    "total_kwh_charged": round(ds.total_kwh_charged, 3),
                    "total_kwh_consumed": round(ds.total_kwh_consumed, 3),
                    "total_cost_czk": round(ds.total_cost_czk, 2),
                    "avg_spot_price": round(ds.avg_spot_price, 4),
                    "avg_total_price": round(ds.avg_total_price, 4),
                    "nt_kwh": round(ds.nt_kwh, 3),
                    "vt_kwh": round(ds.vt_kwh, 3),
                    "charging_sessions": ds.charging_sessions,
                }
        await self._store.async_save(data)
        self._dirty = False

    def record_sample(
        self,
        spot_price: float,
        total_price: float,
        is_nt: bool,
        is_charging: bool,
        consumption_kw: float,
        charging_power_kw: float,
        interval_minutes: float = 2.0,
    ):
        """Record a data sample (called every coordinator update ~2min)."""
        now = datetime.now()
        today_str = now.strftime("%Y-%m-%d")
        hour = now.hour
        hour_str = str(hour)

        if today_str not in self._days:
            self._days[today_str] = DayStat(date=today_str)

        ds = self._days[today_str]
        if hour_str not in ds.hours:
            ds.hours[hour_str] = {
                "kwh_charged": 0, "kwh_consumed": 0, "cost_czk": 0,
                "spot_price_avg": 0, "total_price_avg": 0, "is_nt": is_nt, "samples": 0,
            }

        h = ds.hours[hour_str]
        interval_h = interval_minutes / 60.0

        # Consumption
        cons_kwh = consumption_kw * interval_h
        h["kwh_consumed"] = round(h["kwh_consumed"] + cons_kwh, 4)

        # Charging
        if is_charging:
            charge_kwh = charging_power_kw * interval_h
            h["kwh_charged"] = round(h["kwh_charged"] + charge_kwh, 4)
            h["cost_czk"] = round(h["cost_czk"] + charge_kwh * total_price, 4)

        # Cost for consumption
        h["cost_czk"] = round(h["cost_czk"] + cons_kwh * total_price, 4)

        # Running average of prices
        n = h["samples"]
        h["spot_price_avg"] = round((h["spot_price_avg"] * n + spot_price) / (n + 1), 6)
        h["total_price_avg"] = round((h["total_price_avg"] * n + total_price) / (n + 1), 6)
        h["is_nt"] = is_nt
        h["samples"] = n + 1

        # Recalculate day totals
        ds.recalculate()
        if is_charging and n == 0:
            ds.charging_sessions += 1

        self._dirty = True

    # ── Query methods ─────────────────────────────────────────

    def get_today(self) -> Optional[DayStat]:
        today = datetime.now().strftime("%Y-%m-%d")
        return self._days.get(today)

    def get_day(self, date_str: str) -> Optional[DayStat]:
        return self._days.get(date_str)

    def get_period_summary(self, days_back: int) -> dict:
        """Get summary for last N days."""
        cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        period_days = [ds for d, ds in self._days.items() if d >= cutoff]
        if not period_days:
            return {"days": 0, "total_cost": 0, "total_kwh": 0, "avg_daily_cost": 0}

        total_cost = sum(d.total_cost_czk for d in period_days)
        total_kwh = sum(d.total_kwh_consumed for d in period_days)
        total_charged = sum(d.total_kwh_charged for d in period_days)
        nt_kwh = sum(d.nt_kwh for d in period_days)
        vt_kwh = sum(d.vt_kwh for d in period_days)

        return {
            "days": len(period_days),
            "total_cost_czk": round(total_cost, 2),
            "total_kwh_consumed": round(total_kwh, 1),
            "total_kwh_charged": round(total_charged, 1),
            "avg_daily_cost_czk": round(total_cost / len(period_days), 2),
            "avg_daily_kwh": round(total_kwh / len(period_days), 1),
            "avg_price_czk_kwh": round(total_cost / total_kwh, 4) if total_kwh > 0 else 0,
            "nt_kwh": round(nt_kwh, 1),
            "vt_kwh": round(vt_kwh, 1),
            "nt_share_pct": round(nt_kwh / (nt_kwh + vt_kwh) * 100, 1) if (nt_kwh + vt_kwh) > 0 else 0,
            "charging_sessions": sum(d.charging_sessions for d in period_days),
        }

    def get_daily_costs(self, days_back: int = 30) -> List[dict]:
        """Get daily cost breakdown for charting."""
        cutoff = (datetime.now() - timedelta(days=days_back)).strftime("%Y-%m-%d")
        result = []
        for d_str in sorted(self._days.keys()):
            if d_str >= cutoff:
                ds = self._days[d_str]
                result.append({
                    "date": d_str,
                    "cost_czk": round(ds.total_cost_czk, 2),
                    "kwh_consumed": round(ds.total_kwh_consumed, 1),
                    "kwh_charged": round(ds.total_kwh_charged, 1),
                    "avg_price": round(ds.avg_total_price, 4),
                })
        return result

    def get_hourly_costs_today(self) -> List[dict]:
        """Get hourly cost breakdown for today."""
        ds = self.get_today()
        if not ds:
            return []
        result = []
        for h in range(24):
            hd = ds.hours.get(str(h), {})
            result.append({
                "hour": h,
                "cost_czk": round(hd.get("cost_czk", 0), 2),
                "kwh": round(hd.get("kwh_consumed", 0), 2),
                "spot": round(hd.get("spot_price_avg", 0), 4),
                "total": round(hd.get("total_price_avg", 0), 4),
                "nt": hd.get("is_nt", False),
                "charged": round(hd.get("kwh_charged", 0), 2),
            })
        return result

    def get_month_summary(self, year: int, month: int) -> dict:
        """Get summary for a specific month."""
        prefix = f"{year}-{month:02d}"
        month_days = [ds for d, ds in self._days.items() if d.startswith(prefix)]
        if not month_days:
            return {"month": prefix, "days": 0, "total_cost": 0}
        total_cost = sum(d.total_cost_czk for d in month_days)
        total_kwh = sum(d.total_kwh_consumed for d in month_days)
        return {
            "month": prefix,
            "days": len(month_days),
            "total_cost_czk": round(total_cost, 2),
            "total_kwh": round(total_kwh, 1),
            "avg_daily_cost": round(total_cost / len(month_days), 2),
            "avg_price_czk_kwh": round(total_cost / total_kwh, 4) if total_kwh > 0 else 0,
        }

    def get_all_stats_for_dashboard(self) -> dict:
        """Get comprehensive statistics for dashboard display."""
        today = self.get_today()
        return {
            "today": {
                "cost_czk": round(today.total_cost_czk, 2) if today else 0,
                "kwh_consumed": round(today.total_kwh_consumed, 1) if today else 0,
                "kwh_charged": round(today.total_kwh_charged, 1) if today else 0,
                "avg_price": round(today.avg_total_price, 4) if today else 0,
                "hourly": self.get_hourly_costs_today(),
            },
            "week": self.get_period_summary(7),
            "month": self.get_period_summary(30),
            "year": self.get_period_summary(365),
            "daily_history": self.get_daily_costs(90),
        }
