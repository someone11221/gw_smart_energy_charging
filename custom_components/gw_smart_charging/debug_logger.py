"""Debug logger v3.2.0 — ring buffer of structured events, downloadable from dashboard.

Captures every decision, error, state change with timestamps.
Keeps last 500 events in memory, exportable as JSON/text.
"""
from datetime import datetime
from typing import List, Optional
from dataclasses import dataclass, field, asdict
from collections import deque
import logging
import json

_LOGGER = logging.getLogger(__name__)

# Event severity levels
DEBUG = "debug"
INFO = "info"
WARN = "warn"
ERROR = "error"
ACTION = "action"  # charging started/stopped, plan created


@dataclass
class DebugEvent:
    timestamp: str
    level: str
    category: str  # "prices", "battery", "hdo", "plan", "charging", "config", "stats"
    message: str
    details: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)

    def to_line(self):
        det = ""
        if self.details:
            det = " | " + " ".join(f"{k}={v}" for k, v in self.details.items())
        return f"[{self.timestamp}] [{self.level.upper():6s}] [{self.category:10s}] {self.message}{det}"


class DebugLogger:
    """Ring-buffer debug logger for Smart Charging."""

    MAX_EVENTS = 500

    def __init__(self):
        self._events: deque = deque(maxlen=self.MAX_EVENTS)
        self._error_count = 0
        self._warn_count = 0
        self._action_count = 0
        self._started = datetime.now().isoformat()

    def _add(self, level: str, category: str, message: str, details: dict = None):
        ev = DebugEvent(
            timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            level=level,
            category=category,
            message=message,
            details=details or {},
        )
        self._events.append(ev)
        if level == ERROR:
            self._error_count += 1
        elif level == WARN:
            self._warn_count += 1
        elif level == ACTION:
            self._action_count += 1

    def debug(self, category: str, message: str, **details):
        self._add(DEBUG, category, message, details)

    def info(self, category: str, message: str, **details):
        self._add(INFO, category, message, details)
        _LOGGER.info(f"[{category}] {message}")

    def warn(self, category: str, message: str, **details):
        self._add(WARN, category, message, details)
        _LOGGER.warning(f"[{category}] {message}")

    def error(self, category: str, message: str, **details):
        self._add(ERROR, category, message, details)
        _LOGGER.error(f"[{category}] {message}")

    def action(self, category: str, message: str, **details):
        self._add(ACTION, category, message, details)
        _LOGGER.info(f"[ACTION/{category}] {message}")

    def get_events(self, level: str = None, category: str = None,
                   limit: int = 200) -> List[dict]:
        """Get filtered events as dicts."""
        events = list(self._events)
        if level:
            events = [e for e in events if e.level == level]
        if category:
            events = [e for e in events if e.category == category]
        return [e.to_dict() for e in events[-limit:]]

    def get_text(self, limit: int = 300) -> str:
        """Get events as readable text log."""
        lines = [
            f"=== Smart Charging Debug Log ===",
            f"Started: {self._started}",
            f"Events: {len(self._events)} (errors={self._error_count}, "
            f"warnings={self._warn_count}, actions={self._action_count})",
            f"Export: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
        ]
        for ev in list(self._events)[-limit:]:
            lines.append(ev.to_line())
        return "\n".join(lines)

    def get_json(self, limit: int = 300) -> str:
        """Get events as JSON string."""
        return json.dumps({
            "started": self._started,
            "exported": datetime.now().isoformat(),
            "total_events": len(self._events),
            "error_count": self._error_count,
            "warn_count": self._warn_count,
            "action_count": self._action_count,
            "events": self.get_events(limit=limit),
        }, indent=2, default=str)

    def get_summary(self) -> dict:
        """Short summary for dashboard cards."""
        recent_errors = [e.to_dict() for e in self._events
                         if e.level in (ERROR, WARN)][-5:]
        recent_actions = [e.to_dict() for e in self._events
                          if e.level == ACTION][-5:]
        return {
            "total_events": len(self._events),
            "error_count": self._error_count,
            "warn_count": self._warn_count,
            "action_count": self._action_count,
            "started": self._started,
            "recent_errors": recent_errors,
            "recent_actions": recent_actions,
            "last_event": self._events[-1].to_dict() if self._events else None,
        }
