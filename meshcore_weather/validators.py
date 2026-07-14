"""Input validation helpers for the setup wizard."""

from __future__ import annotations

from meshcore_weather.constants import SUPPORTED_ALERT_TYPES


def normalize_state(value: str) -> str:
    """Normalize a state code to uppercase."""
    return value.strip().upper()


def normalize_county(value: str) -> str:
    """Normalize a county name by stripping whitespace."""
    return " ".join(value.strip().split())


def validate_latitude(value: int | float | str) -> float:
    """Return a validated latitude value."""
    try:
        parsed = float(str(value).strip())
    except ValueError as exc:
        raise ValueError("latitude must be a number") from exc

    if parsed < -90 or parsed > 90:
        raise ValueError("latitude must be between -90 and 90")

    return parsed


def validate_longitude(value: int | float | str) -> float:
    """Return a validated longitude value."""
    try:
        parsed = float(str(value).strip())
    except ValueError as exc:
        raise ValueError("longitude must be a number") from exc

    if parsed < -180 or parsed > 180:
        raise ValueError("longitude must be between -180 and 180")

    return parsed


def validate_poll_interval(value: int | str) -> int:
    """Return a validated poll interval in seconds."""
    try:
        parsed = int(str(value).strip())
    except ValueError as exc:
        raise ValueError("poll interval must be an integer") from exc

    if parsed < 10:
        raise ValueError("poll interval must be at least 10 seconds")

    return parsed


def validate_repeat_interval(value: int | str) -> int:
    """Return a validated repeat interval in minutes."""
    try:
        parsed = int(str(value).strip())
    except ValueError as exc:
        raise ValueError("repeat interval must be an integer") from exc

    if parsed < 1:
        raise ValueError("repeat interval must be at least 1 minute")

    return parsed


def parse_alert_types(raw_value: str) -> list[str]:
    """Parse a comma-separated list of alert type numbers."""
    if not raw_value.strip():
        return []

    selected: list[str] = []
    for token in raw_value.split(","):
        cleaned = token.strip()
        if not cleaned:
            continue
        try:
            index = int(cleaned)
        except ValueError as exc:
            raise ValueError(f"invalid alert type selection: {cleaned}") from exc

        if 1 <= index <= len(SUPPORTED_ALERT_TYPES):
            selected.append(SUPPORTED_ALERT_TYPES[index - 1])
            continue

        raise ValueError(f"alert type number out of range: {index}")

    return selected
