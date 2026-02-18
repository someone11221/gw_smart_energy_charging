"""Main coordinator for Smart Battery Charging Controller v3.2.0."""
from datetime import datetime, timedelta
from typing import Optional
import logging

from homeassistant.core import HomeAssistant
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator

from .const import DOMAIN, VERSION, SLOT_MINUTES
from .price_providers.base import PriceProvider
from .price_providers.ote import OTEPriceProvider
from .price_providers.nanogreen import NanogreenPriceProvider
from .battery_controllers.base import BatteryController
from .battery_controllers.goodwe import GoodWeController
from .charging_strategies.intelligent import IntelligentChargingStrategy, ChargingPlan
from .distribution_tariffs import (
    get_distribution_rate, get_tariff_data, get_monthly_fixed_charge,
    is_nt_hour, COMMON_REGULATED_PER_KWH, DISTRIBUTOR_OPTIONS,
)
from .consumption_predictor import ConsumptionPredictor
from .hdo_reader import HDOReader
from .statistics_tracker import StatisticsTracker
from .debug_logger import DebugLogger

_LOGGER = logging.getLogger(__name__)
UPDATE_INTERVAL = timedelta(minutes=2)

# Fallback: if no price data for this many minutes, use emergency schedule
FALLBACK_TIMEOUT_MIN = 120
FALLBACK_HOURS = [(1, 5), (13, 15)]  # Emergency NT charging windows


class SmartChargingCoordinator(DataUpdateCoordinator):

    def __init__(self, hass: HomeAssistant, config: dict, entry_id: str):
        super().__init__(hass, _LOGGER, name="Smart Battery Charging", update_interval=UPDATE_INTERVAL)
        self.config = dict(config)
        self._entry_id = entry_id
        self._auto_charging_enabled = config.get("auto_charging", True)
        self.config.setdefault("home_consumption_kw", 0.8)

        # Debug logger
        self.dbg = DebugLogger()

        # Price provider
        ptype = config.get("price_provider", "ote")
        self.price_provider: PriceProvider = (
            NanogreenPriceProvider(hass, config) if ptype == "nanogreen"
            else OTEPriceProvider(hass, config))

        # Battery controller
        self.battery_controller: BatteryController = GoodWeController(hass, config)

        # Consumption predictor
        self.consumption_predictor = ConsumptionPredictor(hass, config)

        # HDO reader
        self.hdo_reader = HDOReader(hass, config)

        # Statistics tracker
        self.stats_tracker = StatisticsTracker(hass, entry_id)

        # Strategy
        self.strategy = IntelligentChargingStrategy(config)

        # State
        self.current_plan: Optional[ChargingPlan] = None
        self.last_plan_update: Optional[datetime] = None
        self._charging_active = False
        self._last_price_data: Optional[datetime] = None
        self._fallback_active = False

        self.dbg.info("config", f"Coordinator v{VERSION} initialized",
                      provider=ptype,
                      distributor=config.get("distributor", "egd"),
                      tariff=config.get("tariff", "d57d"),
                      hdo=config.get("hdo_sensor", "sensor.egdtar"),
                      prediction=config.get("prediction_mode", "adaptive"))

    async def async_initialize(self):
        await self.stats_tracker.async_load()
        self.dbg.info("stats", "Statistics loaded from persistent storage")

    def _dist(self):
        return (self.config.get("distributor", "egd"),
                self.config.get("tariff", "d57d"),
                self.config.get("circuit_breaker", "3x25A"))

    def _total_price(self, spot: float, hour: int, dt: datetime = None) -> float:
        d, t, b = self._dist()
        is_weekend = (dt or datetime.now()).weekday() >= 5
        return get_distribution_rate(spot, hour, is_weekend, d, t)

    def _is_nt_now(self) -> bool:
        hdo = self.hdo_reader.is_nt_now()
        if hdo is not None:
            return hdo
        d, t, _ = self._dist()
        return is_nt_hour(d, t, datetime.now().hour, datetime.now().weekday() >= 5)

    def _is_fallback_needed(self) -> bool:
        """Check if we need emergency fallback (no price data too long)."""
        if self._last_price_data is None:
            return True
        elapsed = (datetime.now() - self._last_price_data).total_seconds() / 60
        return elapsed > FALLBACK_TIMEOUT_MIN

    def _is_fallback_charging_window(self) -> bool:
        """Check if current hour is in emergency charging window."""
        h = datetime.now().hour
        for start, end in FALLBACK_HOURS:
            if start <= h < end:
                return True
        return False

    async def _async_update_data(self):
        errors = []

        # Update sources
        for name, coro in [
            ("prices", self.price_provider.async_update()),
            ("battery", self.battery_controller.async_update()),
            ("consumption", self.consumption_predictor.async_update()),
        ]:
            try:
                await coro
                self.dbg.debug(name, f"{name} updated OK")
            except Exception as e:
                errors.append(f"{name}: {e}")
                self.dbg.error(name, f"Update failed: {e}")

        # HDO check
        try:
            current_nt = self._is_nt_now()
            self.dbg.debug("hdo", f"NT={current_nt}")
        except Exception as e:
            current_nt = False
            errors.append(f"hdo: {e}")
            self.dbg.error("hdo", f"HDO check failed: {e}")

        # Check price data freshness
        current_price = None
        price_forecast = {}
        try:
            current_price = await self.price_provider.get_current_price()
            fc = await self.price_provider.get_forecast(48)
            if fc and fc.prices:
                self._last_price_data = datetime.now()
                self._fallback_active = False
                price_forecast = {
                    "prices": [
                        {"time": p.timestamp.strftime("%Y-%m-%d %H:%M"),
                         "price": round(p.price, 6),
                         "total_price": round(self._total_price(p.price, p.timestamp.hour, p.timestamp), 4)}
                        for p in fc.prices
                    ],
                    "min": round(fc.min_price, 4),
                    "max": round(fc.max_price, 4),
                    "avg": round(fc.avg_price, 4),
                }
                self.dbg.debug("prices", f"Got {len(fc.prices)} prices, current={current_price}")
            else:
                self.dbg.warn("prices", "No price data returned from provider")
        except Exception as e:
            errors.append(f"prices: {e}")
            self.dbg.error("prices", f"Price fetch failed: {e}")

        # Fallback mode detection
        if self._is_fallback_needed():
            if not self._fallback_active:
                self._fallback_active = True
                self.dbg.warn("fallback",
                    f"No price data for >{FALLBACK_TIMEOUT_MIN}min, activating emergency schedule",
                    windows=str(FALLBACK_HOURS))
            errors.append(f"FALLBACK: no price data since {self._last_price_data or 'never'}")

        # Plan creation
        if (not self.current_plan or not self.last_plan_update
                or (datetime.now() - self.last_plan_update).total_seconds() > 900):
            try:
                await self._create_new_plan()
                if self.current_plan:
                    self.dbg.action("plan",
                        f"New plan: {len(self.current_plan.slots)} slots, "
                        f"{self.current_plan.total_kwh:.1f} kWh, "
                        f"{self.current_plan.total_cost:.2f} CZK",
                        slots=len(self.current_plan.slots))
            except Exception as e:
                errors.append(f"plan: {e}")
                self.dbg.error("plan", f"Plan creation failed: {e}")

        # Execute charging decision (normal or fallback)
        if self._auto_charging_enabled:
            try:
                if self._fallback_active:
                    await self._execute_fallback_charging()
                elif self.current_plan:
                    await self._execute_charging_decision()
            except Exception as e:
                self.dbg.error("charging", f"Charging decision error: {e}")

        # Battery status log
        bs = self.battery_controller._status
        if bs:
            self.dbg.debug("battery", f"SOC={bs.soc:.1f}% power={bs.power:.0f}W "
                f"{'charging' if bs.charging else 'discharging' if bs.discharging else 'idle'}")

        # Consumption
        consumption_hourly = []
        consumption_summary = {}
        try:
            profile = self.consumption_predictor.get_profile()
            if profile:
                consumption_summary = {
                    "total_24h_kwh": round(profile.total_kwh_24h, 1),
                    "avg_kw": round(profile.avg_power_kw, 2),
                    "peak_kw": round(profile.peak_power_kw, 2),
                    "source": "history" if self.consumption_predictor._last_update else "heuristic",
                    "mode": self.config.get("prediction_mode", "adaptive"),
                }
                now = datetime.now().replace(minute=0, second=0, microsecond=0)
                for i in range(48):
                    t = now + timedelta(hours=i)
                    kw = profile.get_power_at(t.hour)
                    consumption_hourly.append({
                        "time": t.strftime("%Y-%m-%d %H:%M"), "kw": round(kw, 2)})
        except Exception as e:
            self.dbg.debug("consumption", f"Consumption error: {e}")

        # Tariff info
        d, t, b = self._dist()
        tariff_info = {"distributor": d.upper(), "tariff": t, "breaker": b,
                       "current_nt": current_nt}
        try:
            tariff_info["monthly_fixed"] = round(get_monthly_fixed_charge(d, b), 0)
            td = get_tariff_data(d, t)
            if td:
                tariff_info.update({
                    "name": td.name, "vt_rate": td.dist_vt, "nt_rate": td.dist_nt,
                    "regulated": round(COMMON_REGULATED_PER_KWH, 4),
                    "total_vt": round(td.dist_vt + COMMON_REGULATED_PER_KWH, 4),
                    "total_nt": round(td.dist_nt + COMMON_REGULATED_PER_KWH, 4),
                })
        except Exception as e:
            self.dbg.warn("tariff", f"Tariff info error: {e}")
            tariff_info["error"] = str(e)

        # Record statistics
        try:
            cons_kw = 0.8
            try:
                profile = self.consumption_predictor.get_profile()
                if profile:
                    cons_kw = profile.get_power_at(datetime.now().hour)
            except Exception:
                pass
            if current_price is not None:
                tp = self._total_price(current_price, datetime.now().hour)
                self.stats_tracker.record_sample(
                    spot_price=current_price, total_price=tp, is_nt=current_nt,
                    is_charging=self._charging_active, consumption_kw=cons_kw,
                    charging_power_kw=self.config.get("charging_power", 5.0),
                    interval_minutes=UPDATE_INTERVAL.total_seconds() / 60)
        except Exception as e:
            self.dbg.debug("stats", f"Stats recording error: {e}")

        # Periodic save
        if datetime.now().minute % 10 == 0:
            try:
                await self.stats_tracker.async_save()
            except Exception:
                pass

        # HDO + stats info
        try:
            hdo_info = self.hdo_reader.get_diagnostics()
        except Exception:
            hdo_info = {}
        try:
            stats_data = self.stats_tracker.get_all_stats_for_dashboard()
        except Exception:
            stats_data = {}

        return {
            "battery_status": self.battery_controller._status,
            "current_price": current_price,
            "price_forecast": price_forecast,
            "charging_plan": self.current_plan,
            "charging_active": self._charging_active,
            "auto_enabled": self._auto_charging_enabled,
            "consumption_forecast": consumption_summary,
            "consumption_hourly": consumption_hourly,
            "tariff_info": tariff_info,
            "hdo": hdo_info,
            "statistics": stats_data,
            "flat_price_compare": self.config.get("flat_price_compare", 4.5),
            "fallback_active": self._fallback_active,
            "debug_summary": self.dbg.get_summary(),
            "last_update": datetime.now(),
            "version": VERSION,
            "errors": errors,
        }

    async def _create_new_plan(self):
        bs = self.battery_controller._status
        fc = await self.price_provider.get_forecast(48)
        if not bs or not fc:
            self.dbg.debug("plan", f"Cannot create plan: battery={'OK' if bs else 'None'}, forecast={'OK' if fc else 'None'}")
            return
        self.current_plan = await self.strategy.create_charging_plan(
            battery_status=bs, price_forecast=fc,
            solar_forecast=None, consumption_predictor=self.consumption_predictor)
        self.last_plan_update = datetime.now()

    async def _execute_charging_decision(self):
        if not self.current_plan:
            return
        should, reason = self.strategy.should_charge_now(self.current_plan)
        if should != self._charging_active:
            if should:
                if await self.battery_controller.start_charging():
                    self._charging_active = True
                    self.dbg.action("charging", f"STARTED: {reason}")
            else:
                if await self.battery_controller.stop_charging():
                    self._charging_active = False
                    self.dbg.action("charging", f"STOPPED: {reason}")

    async def _execute_fallback_charging(self):
        """Emergency charging when no price data available."""
        should = self._is_fallback_charging_window()
        bs = self.battery_controller._status
        # Only charge if SOC is low
        if bs and bs.soc > 90:
            should = False
        if should != self._charging_active:
            if should:
                if await self.battery_controller.start_charging():
                    self._charging_active = True
                    self.dbg.action("fallback", "EMERGENCY charging started (no price data)",
                                    soc=bs.soc if bs else None)
            else:
                if await self.battery_controller.stop_charging():
                    self._charging_active = False
                    self.dbg.action("fallback", "EMERGENCY charging stopped")

    async def set_auto_charging(self, enabled: bool):
        self._auto_charging_enabled = enabled
        self.dbg.action("config", f"Auto charging {'ENABLED' if enabled else 'DISABLED'}")
        if not enabled and self._charging_active:
            await self.battery_controller.stop_charging()
            self._charging_active = False
            self.dbg.action("charging", "Charging stopped (auto disabled)")

    async def force_plan_update(self):
        self.dbg.info("plan", "Manual plan refresh requested")
        await self._create_new_plan()
        await self.async_request_refresh()

    def get_statistics(self) -> dict:
        d, t, b = self._dist()
        stats = {"version": VERSION, "provider": self.price_provider.name,
                 "controller": self.battery_controller.name,
                 "auto_enabled": self._auto_charging_enabled,
                 "charging_active": self._charging_active,
                 "distributor": d, "tariff": t, "breaker": b,
                 "prediction_mode": self.config.get("prediction_mode", "adaptive"),
                 "hdo_sensor": self.hdo_reader.sensor_entity,
                 "hdo_state": self.hdo_reader.last_state_str,
                 "fallback_active": self._fallback_active}
        if self.battery_controller._status:
            s = self.battery_controller._status
            stats.update({"soc": s.soc, "power": s.power})
        if self.current_plan:
            p = self.current_plan
            stats.update({"plan_slots": len(p.slots), "plan_kwh": p.total_kwh,
                          "plan_cost": p.total_cost, "plan_confidence": p.confidence})
        try:
            profile = self.consumption_predictor.get_profile()
            if profile:
                stats["consumption_24h"] = profile.total_kwh_24h
        except Exception:
            pass
        return stats
