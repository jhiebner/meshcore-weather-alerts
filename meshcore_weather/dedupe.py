"""Deduplication helpers for weather alerts."""

from __future__ import annotations

from collections import defaultdict
from time import time


class AlertTracker:
    """Track recently seen alert IDs to avoid repeated broadcasts."""

    def __init__(self) -> None:
        self._seen_ids: set[str] = set()
        self._last_broadcast: dict[str, float] = {}

    def should_broadcast(self, alert_id: str, repeat_interval_minutes: int = 15, now: float | None = None) -> bool:
        """Return True when an alert should be broadcast again."""
        current_time = now if now is not None else time()

        if repeat_interval_minutes <= 0:
            if alert_id in self._seen_ids:
                return False
            self._seen_ids.add(alert_id)
            return True

        last_seen = self._last_broadcast.get(alert_id)
        if last_seen is None:
            self._last_broadcast[alert_id] = current_time
            self._seen_ids.add(alert_id)
            return True

        elapsed_minutes = (current_time - last_seen) / 60.0
        if elapsed_minutes < repeat_interval_minutes:
            return False

        self._last_broadcast[alert_id] = current_time
        return True
