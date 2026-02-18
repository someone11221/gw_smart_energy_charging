"""Czech electricity distribution tariffs database.

Data based on ERU price decisions for 2025/2026.
Covers all three Czech distribution areas, common tariff types and circuit breaker sizes.

Structure:
  - Per-kWh regulated charges (distribution VT/NT, system, OZE, tax)
  - NT hour schedules per distributor × tariff
  - Monthly fixed charges per circuit breaker size

Note: Commodity (spot) price is added separately from OTE/Nanogreen.
These are the REGULATED components only.
"""
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
import logging

_LOGGER = logging.getLogger(__name__)

# ── Common regulated charges (same for all distributors, set by ERU / law) ──

# Cena za systémové služby (ČEPS) – CZK/kWh
SYSTEM_SERVICES = 0.074

# Podpora obnovitelných zdrojů energie (POZE) – CZK/kWh
POZE_LEVY = 0.495

# Daň z elektřiny – CZK/kWh  (28.30 CZK/MWh dle zákona)
ELECTRICITY_TAX = 0.02830

# Celkem společné regulované poplatky za kWh
COMMON_REGULATED_PER_KWH = SYSTEM_SERVICES + POZE_LEVY + ELECTRICITY_TAX


@dataclass
class TariffRate:
    """Per-kWh distribution rate for a specific tariff."""
    name: str                     # Human-readable tariff name
    code: str                     # e.g. "d57d"
    has_nt: bool                  # Whether tariff has low-tariff (NT) period
    dist_vt: float                # Distribution VT rate CZK/kWh
    dist_nt: float                # Distribution NT rate CZK/kWh (0 if no NT)
    nt_hours_daily: int = 0       # Guaranteed NT hours per day
    description: str = ""


@dataclass
class CircuitBreaker:
    """Monthly fixed charge for a circuit breaker size."""
    label: str                    # e.g. "3x25A"
    amperage: int                 # Main value in amps
    phases: int                   # 1 or 3
    monthly_fixed: float          # CZK/month (stálý plat za příkon)


@dataclass
class NTSchedule:
    """NT (low-tariff) hour schedule for a distributor × tariff combination.

    In reality, NT windows are controlled by HDO signals and vary by
    transformer area.  These are *typical / guaranteed minimum* windows.
    Users can override via config.
    """
    # Sets of hours (0-23) that are typically NT
    weekday_nt: Set[int] = field(default_factory=set)
    weekend_nt: Set[int] = field(default_factory=set)
    # 15-min quarter flags: if True, the whole hour counts; otherwise
    # we can define quarter-hour offsets (future extension)


@dataclass
class DistributorData:
    """Complete data for one distribution area."""
    code: str                     # "egd", "cez", "pre"
    name: str                     # "EG.D (EON)"
    tariffs: Dict[str, TariffRate] = field(default_factory=dict)
    circuit_breakers: Dict[str, CircuitBreaker] = field(default_factory=dict)
    nt_schedules: Dict[str, NTSchedule] = field(default_factory=dict)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Circuit breaker sizes (monthly fixed charges)
# Values approximate for D57d tariff; other tariffs may differ slightly.
# The fixed charge doesn't affect per-kWh optimisation but is shown in UI.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

CIRCUIT_BREAKERS: Dict[str, CircuitBreaker] = {
    "1x25A":  CircuitBreaker("1×25 A",  25, 1, monthly_fixed=118.0),
    "3x20A":  CircuitBreaker("3×20 A",  20, 3, monthly_fixed=283.0),
    "3x25A":  CircuitBreaker("3×25 A",  25, 3, monthly_fixed=354.0),
    "3x32A":  CircuitBreaker("3×32 A",  32, 3, monthly_fixed=453.0),
    "3x40A":  CircuitBreaker("3×40 A",  40, 3, monthly_fixed=566.0),
    "3x50A":  CircuitBreaker("3×50 A",  50, 3, monthly_fixed=708.0),
    "3x63A":  CircuitBreaker("3×63 A",  63, 3, monthly_fixed=892.0),
    "3x80A":  CircuitBreaker("3×80 A",  80, 3, monthly_fixed=1133.0),
    "3x100A": CircuitBreaker("3×100 A", 100, 3, monthly_fixed=1416.0),
}

# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Tariff definitions – per-kWh distribution rates
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

# ── EG.D (EON) ─────────────────────────────────────────────────────────

_EGD_TARIFFS: Dict[str, TariffRate] = {
    "d02d": TariffRate(
        name="D02d – Jednotarif",
        code="d02d", has_nt=False,
        dist_vt=2.109, dist_nt=0.0,
        description="Jednotarifní sazba pro běžnou spotřebu",
    ),
    "d25d": TariffRate(
        name="D25d – Akumulace 8h",
        code="d25d", has_nt=True,
        dist_vt=2.109, dist_nt=1.298,
        nt_hours_daily=8,
        description="Akumulační spotřebiče, 8 hodin NT denně",
    ),
    "d26d": TariffRate(
        name="D26d – Akumulace víkend",
        code="d26d", has_nt=True,
        dist_vt=2.109, dist_nt=1.298,
        nt_hours_daily=8,
        description="Akumulační spotřebiče + celý víkend NT",
    ),
    "d27d": TariffRate(
        name="D27d – Elektromobil",
        code="d27d", has_nt=True,
        dist_vt=2.109, dist_nt=1.298,
        nt_hours_daily=8,
        description="Nabíjení elektromobilu, 8 hodin NT",
    ),
    "d35d": TariffRate(
        name="D35d – Hybridní vytápění 16h",
        code="d35d", has_nt=True,
        dist_vt=1.847, dist_nt=1.058,
        nt_hours_daily=16,
        description="Hybridní vytápění, 16 hodin NT",
    ),
    "d45d": TariffRate(
        name="D45d – Přímotop 20h",
        code="d45d", has_nt=True,
        dist_vt=1.847, dist_nt=1.058,
        nt_hours_daily=20,
        description="Přímotopné vytápění, 20 hodin NT",
    ),
    "d56d": TariffRate(
        name="D56d – Tepelné čerpadlo 22h",
        code="d56d", has_nt=True,
        dist_vt=1.847, dist_nt=1.058,
        nt_hours_daily=22,
        description="Tepelné čerpadlo, 22 hodin NT denně",
    ),
    "d57d": TariffRate(
        name="D57d – Tepelné čerpadlo 20h",
        code="d57d", has_nt=True,
        dist_vt=1.847, dist_nt=1.058,
        nt_hours_daily=20,
        description="Tepelné čerpadlo, 20 hodin NT denně (nejčastější pro FVE+baterie)",
    ),
    "d61d": TariffRate(
        name="D61d – Víkendový",
        code="d61d", has_nt=True,
        dist_vt=2.109, dist_nt=1.298,
        nt_hours_daily=8,
        description="Víkendová sazba, celý víkend + 8h v pracovní dny",
    ),
}

# ── ČEZ Distribuce ─────────────────────────────────────────────────────

_CEZ_TARIFFS: Dict[str, TariffRate] = {
    "d02d": TariffRate(
        name="D02d – Jednotarif",
        code="d02d", has_nt=False,
        dist_vt=2.242, dist_nt=0.0,
    ),
    "d25d": TariffRate(
        name="D25d – Akumulace 8h",
        code="d25d", has_nt=True,
        dist_vt=2.242, dist_nt=1.358,
        nt_hours_daily=8,
    ),
    "d26d": TariffRate(
        name="D26d – Akumulace víkend",
        code="d26d", has_nt=True,
        dist_vt=2.242, dist_nt=1.358,
        nt_hours_daily=8,
    ),
    "d27d": TariffRate(
        name="D27d – Elektromobil",
        code="d27d", has_nt=True,
        dist_vt=2.242, dist_nt=1.358,
        nt_hours_daily=8,
    ),
    "d35d": TariffRate(
        name="D35d – Hybridní vytápění 16h",
        code="d35d", has_nt=True,
        dist_vt=1.973, dist_nt=1.138,
        nt_hours_daily=16,
    ),
    "d45d": TariffRate(
        name="D45d – Přímotop 20h",
        code="d45d", has_nt=True,
        dist_vt=1.973, dist_nt=1.138,
        nt_hours_daily=20,
    ),
    "d56d": TariffRate(
        name="D56d – Tepelné čerpadlo 22h",
        code="d56d", has_nt=True,
        dist_vt=1.973, dist_nt=1.138,
        nt_hours_daily=22,
    ),
    "d57d": TariffRate(
        name="D57d – Tepelné čerpadlo 20h",
        code="d57d", has_nt=True,
        dist_vt=1.973, dist_nt=1.138,
        nt_hours_daily=20,
    ),
    "d61d": TariffRate(
        name="D61d – Víkendový",
        code="d61d", has_nt=True,
        dist_vt=2.242, dist_nt=1.358,
        nt_hours_daily=8,
    ),
}

# ── PREdistribuce (Praha) ──────────────────────────────────────────────

_PRE_TARIFFS: Dict[str, TariffRate] = {
    "d02d": TariffRate(
        name="D02d – Jednotarif",
        code="d02d", has_nt=False,
        dist_vt=2.015, dist_nt=0.0,
    ),
    "d25d": TariffRate(
        name="D25d – Akumulace 8h",
        code="d25d", has_nt=True,
        dist_vt=2.015, dist_nt=1.245,
        nt_hours_daily=8,
    ),
    "d26d": TariffRate(
        name="D26d – Akumulace víkend",
        code="d26d", has_nt=True,
        dist_vt=2.015, dist_nt=1.245,
        nt_hours_daily=8,
    ),
    "d27d": TariffRate(
        name="D27d – Elektromobil",
        code="d27d", has_nt=True,
        dist_vt=2.015, dist_nt=1.245,
        nt_hours_daily=8,
    ),
    "d35d": TariffRate(
        name="D35d – Hybridní vytápění 16h",
        code="d35d", has_nt=True,
        dist_vt=1.765, dist_nt=0.998,
        nt_hours_daily=16,
    ),
    "d45d": TariffRate(
        name="D45d – Přímotop 20h",
        code="d45d", has_nt=True,
        dist_vt=1.765, dist_nt=0.998,
        nt_hours_daily=20,
    ),
    "d56d": TariffRate(
        name="D56d – Tepelné čerpadlo 22h",
        code="d56d", has_nt=True,
        dist_vt=1.765, dist_nt=0.998,
        nt_hours_daily=22,
    ),
    "d57d": TariffRate(
        name="D57d – Tepelné čerpadlo 20h",
        code="d57d", has_nt=True,
        dist_vt=1.765, dist_nt=0.998,
        nt_hours_daily=20,
    ),
    "d61d": TariffRate(
        name="D61d – Víkendový",
        code="d61d", has_nt=True,
        dist_vt=2.015, dist_nt=1.245,
        nt_hours_daily=8,
    ),
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# NT hour schedules (typical HDO windows)
#
# NOTE: Real HDO windows vary by transformer area and are signalled
# dynamically.  These are *representative* schedules.
# Users should verify against their distributor's HDO timetable.
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def _hours(*ranges) -> Set[int]:
    """Helper: build set of hours from (start, end_exclusive) ranges."""
    result: Set[int] = set()
    for start, end in ranges:
        if start <= end:
            result.update(range(start, end))
        else:
            # Wrap around midnight: e.g. (22, 6) → 22,23,0,1,2,3,4,5
            result.update(range(start, 24))
            result.update(range(0, end))
    return result


# Typical NT windows for EG.D (South Moravia / South Bohemia)
_EGD_NT_SCHEDULES: Dict[str, NTSchedule] = {
    "d25d": NTSchedule(
        weekday_nt=_hours((0, 6), (13, 15)),
        weekend_nt=_hours((0, 6), (13, 15)),
    ),
    "d26d": NTSchedule(
        weekday_nt=_hours((0, 6), (13, 15)),
        weekend_nt=_hours((0, 24)),  # Whole weekend
    ),
    "d27d": NTSchedule(
        weekday_nt=_hours((0, 6), (18, 20)),
        weekend_nt=_hours((0, 6), (18, 20)),
    ),
    "d35d": NTSchedule(
        weekday_nt=_hours((0, 6), (9, 12), (14, 17), (20, 24)),
        weekend_nt=_hours((0, 6), (9, 12), (14, 17), (20, 24)),
    ),
    "d45d": NTSchedule(
        weekday_nt=_hours((0, 7), (9, 12), (13, 16), (17, 21), (22, 24)),
        weekend_nt=_hours((0, 7), (9, 12), (13, 16), (17, 21), (22, 24)),
    ),
    "d56d": NTSchedule(
        weekday_nt=_hours((0, 7), (8, 12), (13, 17), (18, 24)),
        weekend_nt=_hours((0, 7), (8, 12), (13, 17), (18, 24)),
    ),
    "d57d": NTSchedule(
        weekday_nt=_hours((0, 6), (9, 12), (14, 17), (19, 24)),
        weekend_nt=_hours((0, 6), (9, 12), (14, 17), (19, 24)),
    ),
    "d61d": NTSchedule(
        weekday_nt=_hours((0, 6), (13, 15)),
        weekend_nt=_hours((0, 24)),
    ),
}

# Typical NT windows for ČEZ Distribuce
_CEZ_NT_SCHEDULES: Dict[str, NTSchedule] = {
    "d25d": NTSchedule(
        weekday_nt=_hours((0, 6), (12, 14)),
        weekend_nt=_hours((0, 6), (12, 14)),
    ),
    "d26d": NTSchedule(
        weekday_nt=_hours((0, 6), (12, 14)),
        weekend_nt=_hours((0, 24)),
    ),
    "d27d": NTSchedule(
        weekday_nt=_hours((0, 6), (18, 20)),
        weekend_nt=_hours((0, 6), (18, 20)),
    ),
    "d35d": NTSchedule(
        weekday_nt=_hours((0, 6), (10, 13), (14, 17), (20, 24)),
        weekend_nt=_hours((0, 6), (10, 13), (14, 17), (20, 24)),
    ),
    "d45d": NTSchedule(
        weekday_nt=_hours((0, 7), (8, 12), (13, 16), (18, 22), (23, 24)),
        weekend_nt=_hours((0, 7), (8, 12), (13, 16), (18, 22), (23, 24)),
    ),
    "d56d": NTSchedule(
        weekday_nt=_hours((0, 8), (9, 12), (13, 17), (18, 24)),
        weekend_nt=_hours((0, 8), (9, 12), (13, 17), (18, 24)),
    ),
    "d57d": NTSchedule(
        weekday_nt=_hours((0, 6), (10, 13), (14, 17), (20, 24)),
        weekend_nt=_hours((0, 6), (10, 13), (14, 17), (20, 24)),
    ),
    "d61d": NTSchedule(
        weekday_nt=_hours((0, 6), (12, 14)),
        weekend_nt=_hours((0, 24)),
    ),
}

# Typical NT windows for PREdistribuce (Prague)
_PRE_NT_SCHEDULES: Dict[str, NTSchedule] = {
    "d25d": NTSchedule(
        weekday_nt=_hours((0, 6), (11, 13)),
        weekend_nt=_hours((0, 6), (11, 13)),
    ),
    "d26d": NTSchedule(
        weekday_nt=_hours((0, 6), (11, 13)),
        weekend_nt=_hours((0, 24)),
    ),
    "d27d": NTSchedule(
        weekday_nt=_hours((0, 6), (18, 20)),
        weekend_nt=_hours((0, 6), (18, 20)),
    ),
    "d35d": NTSchedule(
        weekday_nt=_hours((0, 6), (10, 13), (14, 17), (21, 24)),
        weekend_nt=_hours((0, 6), (10, 13), (14, 17), (21, 24)),
    ),
    "d45d": NTSchedule(
        weekday_nt=_hours((0, 7), (9, 12), (13, 17), (18, 22), (23, 24)),
        weekend_nt=_hours((0, 7), (9, 12), (13, 17), (18, 22), (23, 24)),
    ),
    "d56d": NTSchedule(
        weekday_nt=_hours((0, 7), (8, 12), (13, 17), (18, 24)),
        weekend_nt=_hours((0, 7), (8, 12), (13, 17), (18, 24)),
    ),
    "d57d": NTSchedule(
        weekday_nt=_hours((0, 6), (10, 13), (14, 17), (20, 24)),
        weekend_nt=_hours((0, 6), (10, 13), (14, 17), (20, 24)),
    ),
    "d61d": NTSchedule(
        weekday_nt=_hours((0, 6), (11, 13)),
        weekend_nt=_hours((0, 24)),
    ),
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Aggregated distributor data
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

DISTRIBUTORS: Dict[str, DistributorData] = {
    "egd": DistributorData(
        code="egd",
        name="EG.D (EON)",
        tariffs=_EGD_TARIFFS,
        circuit_breakers=CIRCUIT_BREAKERS,
        nt_schedules=_EGD_NT_SCHEDULES,
    ),
    "cez": DistributorData(
        code="cez",
        name="ČEZ Distribuce",
        tariffs=_CEZ_TARIFFS,
        circuit_breakers=CIRCUIT_BREAKERS,
        nt_schedules=_CEZ_NT_SCHEDULES,
    ),
    "pre": DistributorData(
        code="pre",
        name="PREdistribuce (Praha)",
        tariffs=_PRE_TARIFFS,
        circuit_breakers=CIRCUIT_BREAKERS,
        nt_schedules=_PRE_NT_SCHEDULES,
    ),
}

# UI selection lists
DISTRIBUTOR_OPTIONS = {k: v.name for k, v in DISTRIBUTORS.items()}
TARIFF_OPTIONS = {k: v.name for k, v in _EGD_TARIFFS.items()}   # Names are the same
BREAKER_OPTIONS = {k: v.label for k, v in CIRCUIT_BREAKERS.items()}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# Public helper functions used by the strategy engine
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_tariff_data(
    distributor: str, tariff: str
) -> Optional[TariffRate]:
    """Get tariff rate data for a distributor × tariff combination."""
    dist = DISTRIBUTORS.get(distributor)
    if not dist:
        _LOGGER.warning(f"Unknown distributor: {distributor}")
        return None
    rate = dist.tariffs.get(tariff)
    if not rate:
        _LOGGER.warning(f"Unknown tariff {tariff} for {distributor}")
        return None
    return rate


def get_nt_schedule(
    distributor: str, tariff: str
) -> Optional[NTSchedule]:
    """Get NT hour schedule for a distributor × tariff."""
    dist = DISTRIBUTORS.get(distributor)
    if not dist:
        return None
    return dist.nt_schedules.get(tariff)


def is_nt_hour(
    distributor: str, tariff: str, hour: int, is_weekend: bool
) -> bool:
    """Check if a given hour falls in the NT (low-tariff) period."""
    schedule = get_nt_schedule(distributor, tariff)
    if not schedule:
        return False
    if is_weekend:
        return hour in schedule.weekend_nt
    return hour in schedule.weekday_nt


def get_distribution_rate(
    spot_price: float,
    hour: int,
    is_weekend: bool,
    distributor: str = "egd",
    tariff: str = "d57d",
) -> float:
    """Calculate total per-kWh price including distribution + regulated charges.

    Args:
        spot_price: OTE spot price in CZK/kWh
        hour: Hour of day (0-23)
        is_weekend: True for Saturday/Sunday
        distributor: Distributor code
        tariff: Tariff code

    Returns:
        Total price CZK/kWh
    """
    rate = get_tariff_data(distributor, tariff)
    if not rate:
        # Fallback: use approximate values
        _LOGGER.debug("Using fallback distribution rate")
        dist = 1.058 if hour in _hours((22, 6), (9, 12), (14, 17), (19, 24)) else 1.847
        return round(spot_price + dist + COMMON_REGULATED_PER_KWH, 6)

    nt = is_nt_hour(distributor, tariff, hour, is_weekend)
    dist = rate.dist_nt if nt else rate.dist_vt

    return round(spot_price + dist + COMMON_REGULATED_PER_KWH, 6)


def get_distribution_rate_15min(
    spot_price: float,
    hour: int,
    minute: int,
    is_weekend: bool,
    distributor: str = "egd",
    tariff: str = "d57d",
) -> float:
    """Calculate total price for a 15-minute interval.

    For now, NT determination is per-hour. In the future, HDO 15-min
    granularity can be added here.
    """
    return get_distribution_rate(spot_price, hour, is_weekend, distributor, tariff)


def get_monthly_fixed_charge(
    distributor: str = "egd",
    breaker: str = "3x25A",
) -> float:
    """Get monthly fixed charge for circuit breaker size."""
    cb = CIRCUIT_BREAKERS.get(breaker)
    return cb.monthly_fixed if cb else 354.0
