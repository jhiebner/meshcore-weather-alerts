"""Deduplication helpers for weather alerts."""

from __future__ import annotations


class AlertTracker:
    """Track recently seen alert IDs to avoid repeated broadcasts."""

    def __init__(self) -> None:
        self._seen_ids: set[str] = set()

    def should_broadcast(self, alert_id: str) -> bool:
        """Return True for a new alert ID and remember it."""
        if alert_id in self._seen_ids:
            return False

        self._seen_ids.add(alert_id)
        return True
