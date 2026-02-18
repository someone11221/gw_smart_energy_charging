"""HDO (hromadné dálkové ovládání) signal reader.

Reads real-time NT/VT tariff signal from a Home Assistant sensor.
Default: sensor.egdtar (on=NT low tariff, off=VT high tariff).
Falls back to static schedule from distribution_tariffs if sensor unavailable.
"""
from datetime import datetime
from typing import Optional, Set
import logging

from homeassistant.core import HomeAssistant

_LOGGER = logging.getLogger(__name__)

# States that mean NT (low tariff) is active
NT_ON_STATES = {"on", "true", "1", "low", "nt", "yes", "active", "nizky", "nízký"}
VT_STATES = {"off", "false", "0", "high", "vt", "no", "inactive", "vysoky", "vysoký"}


class HDOReader:
    """Reads HDO signal to determine current NT/VT tariff period."""

    def __init__(self, hass: HomeAssistant, config: dict):
        self.hass = hass
        self._sensor = config.get("hdo_sensor", "sensor.egdtar")
        self._last_state: Optional[bool] = None  # True=NT, False=VT
        self._last_read: Optional[datetime] = None
        # Schedule of when we observed NT/VT transitions for smarter prediction
        self._observed_nt_hours: Set[int] = set()
        self._observed_vt_hours: Set[int] = set()
        self._observation_days = 0

    def is_sensor_available(self) -> bool:
        """Check if HDO sensor exists and is not unavailable."""
        if not self._sensor:
            return False
        state = self.hass.states.get(self._sensor)
        return state is not None and state.state not in ("unknown", "unavailable", "")

    def is_nt_now(self) -> Optional[bool]:
        """Check if current tariff is NT (low).

        Returns:
            True = NT active (low tariff)
            False = VT active (high tariff)
            None = sensor unavailable (use fallback)
        """
        if not self._sensor:
            return None

        state = self.hass.states.get(self._sensor)
        if state is None or state.state in ("unknown", "unavailable", ""):
            _LOGGER.debug(f"HDO sensor {self._sensor} unavailable")
            return None

        val = state.state.strip().lower()
        now = datetime.now()

        if val in NT_ON_STATES:
            self._last_state = True
            self._last_read = now
            self._observed_nt_hours.add(now.hour)
            return True
        elif val in VT_STATES:
            self._last_state = False
            self._last_read = now
            self._observed_vt_hours.add(now.hour)
            return False
        else:
            # Try numeric
            try:
                num = float(val)
                result = num > 0
                self._last_state = result
                self._last_read = now
                if result:
                    self._observed_nt_hours.add(now.hour)
                else:
                    self._observed_vt_hours.add(now.hour)
                return result
            except (ValueError, TypeError):
                _LOGGER.warning(f"HDO sensor {self._sensor}: unrecognized state '{val}'")
                return None

    def predict_nt_at_hour(self, hour: int) -> Optional[bool]:
        """Predict if hour will be NT based on observed pattern.

        Returns None if insufficient data.
        """
        if hour in self._observed_nt_hours and hour not in self._observed_vt_hours:
            return True
        if hour in self._observed_vt_hours and hour not in self._observed_nt_hours:
            return False
        return None  # ambiguous or no data

    def get_observed_nt_hours(self) -> Set[int]:
        """Return set of hours observed as NT."""
        return self._observed_nt_hours.copy()

    @property
    def sensor_entity(self) -> str:
        return self._sensor

    @property
    def last_state_str(self) -> str:
        if self._last_state is None:
            return "unknown"
        return "NT (nízký)" if self._last_state else "VT (vysoký)"

    def get_diagnostics(self) -> dict:
        return {
            "sensor": self._sensor,
            "available": self.is_sensor_available(),
            "current": self.last_state_str,
            "observed_nt_hours": sorted(self._observed_nt_hours),
            "observed_vt_hours": sorted(self._observed_vt_hours),
            "last_read": self._last_read.isoformat() if self._last_read else None,
        }
