"""Configuration management for the MeshCore Weather Gateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class GatewayConfig:
    """Runtime configuration for the gateway."""

    serial_port: str = ""
    latitude: float | None = None
    longitude: float | None = None
    tracked_locations: list[dict[str, str]] = field(default_factory=list)
    alert_types: list[str] = field(default_factory=list)
    poll_interval_seconds: int = 60
    repeat_interval_minutes: int = 15
    meshcore_channel: str = "#weather-alert"
    logging_level: str = "INFO"

    def validate(self) -> list[str]:
        """Return validation errors for the configuration."""
        errors: list[str] = []

        if not self.serial_port.strip():
            errors.append("serial_port")

        if self.latitude is None:
            errors.append("latitude")

        if self.longitude is None:
            errors.append("longitude")

        if not self.alert_types:
            errors.append("alert_types")

        if self.poll_interval_seconds < 10:
            errors.append("poll_interval_seconds")

        if self.repeat_interval_minutes < 0:
            errors.append("repeat_interval_minutes")

        return errors


def save_config(config: GatewayConfig, path: Path | str | None = None) -> Path:
    """Save configuration to a YAML file."""
    destination = Path(path) if path is not None else Path("config.yaml")
    destination.write_text(
        yaml.safe_dump(
            {
                "meshcore": {
                    "serial_port": config.serial_port,
                    "channel": config.meshcore_channel,
                },
                "weather": {
                    "latitude": config.latitude,
                    "longitude": config.longitude,
                    "tracked_locations": config.tracked_locations,
                    "alert_types": config.alert_types,
                },
                "schedule": {
                    "poll_interval_seconds": config.poll_interval_seconds,
                    "repeat_interval_minutes": config.repeat_interval_minutes,
                },
                "logging": {"level": config.logging_level},
            },
            sort_keys=False,
        ),
        encoding="utf-8",
    )
    return destination


def load_config(path: Path | str | None = None) -> GatewayConfig:
    """Load configuration from a YAML file."""
    source = Path(path) if path is not None else Path("config.yaml")

    if not source.exists():
        return GatewayConfig()

    with source.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle) or {}

    meshcore = data.get("meshcore", {})
    weather = data.get("weather", {})
    schedule = data.get("schedule", {})
    logging_ = data.get("logging", {})

    return GatewayConfig(
        serial_port=str(meshcore.get("serial_port", "")),
        latitude=float(weather.get("latitude", 0)) if str(weather.get("latitude", "")).strip() else None,
        longitude=float(weather.get("longitude", 0)) if str(weather.get("longitude", "")).strip() else None,
        tracked_locations=list(weather.get("tracked_locations", [])),
        alert_types=list(weather.get("alert_types", [])),
        poll_interval_seconds=int(schedule.get("poll_interval_seconds", 60)),
        repeat_interval_minutes=int(schedule.get("repeat_interval_minutes", 15)),
        meshcore_channel=str(meshcore.get("channel", "#weather-alert")),
        logging_level=str(logging_.get("level", "INFO")),
    )
