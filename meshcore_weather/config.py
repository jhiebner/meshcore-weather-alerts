"""Configuration management for the MeshCore Weather Gateway."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass(frozen=True)
class ValidationCheck:
    """Human-friendly validation result for a single config field."""

    field: str
    label: str
    value: str
    passed: bool
    message: str | None = None


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
    meshcore_channel: str = "#weather-alerts"
    logging_level: str = "INFO"

    def validation_checks(self) -> list[ValidationCheck]:
        """Return detailed validation results for the configuration."""
        tracked_locations = ", ".join(
            f"{location.get('name', 'Unnamed')} ({location.get('state', '').strip() or 'Unknown state'})"
            for location in self.tracked_locations
            if isinstance(location, dict)
        )

        checks = [
            ValidationCheck(
                field="serial_port",
                label="MeshCore serial port",
                value=self.serial_port or "Not set",
                passed=bool(self.serial_port.strip()),
                message="A serial port is required.",
            ),
            ValidationCheck(
                field="latitude",
                label="Latitude",
                value=str(self.latitude) if self.latitude is not None else "Not set",
                passed=self.latitude is not None,
                message="A latitude is required.",
            ),
            ValidationCheck(
                field="longitude",
                label="Longitude",
                value=str(self.longitude) if self.longitude is not None else "Not set",
                passed=self.longitude is not None,
                message="A longitude is required.",
            ),
            ValidationCheck(
                field="alert_types",
                label="Alert types",
                value=", ".join(self.alert_types) if self.alert_types else "None selected",
                passed=bool(self.alert_types),
                message="At least one alert type must be selected.",
            ),
            ValidationCheck(
                field="poll_interval_seconds",
                label="Poll interval",
                value=f"{self.poll_interval_seconds} seconds",
                passed=self.poll_interval_seconds >= 10,
                message="The poll interval must be at least 10 seconds.",
            ),
            ValidationCheck(
                field="repeat_interval_minutes",
                label="Repeat interval",
                value=f"{self.repeat_interval_minutes} minutes",
                passed=self.repeat_interval_minutes >= 0,
                message="The repeat interval must be 0 or greater.",
            ),
        ]

        if self.tracked_locations:
            checks.append(
                ValidationCheck(
                    field="tracked_locations",
                    label="Tracked locations",
                    value=tracked_locations or "Configured",
                    passed=True,
                    message=None,
                )
            )

        return checks

    def validate(self) -> list[str]:
        """Return validation errors for the configuration."""
        return [check.field for check in self.validation_checks() if not check.passed]


def build_configuration_summary(config: GatewayConfig) -> str:
    """Create a short human-friendly summary of the configuration."""
    lines = [
        "Configuration summary",
        f"- MeshCore serial port: {config.serial_port or 'Not set'}",
        f"- Latitude: {config.latitude if config.latitude is not None else 'Not set'}",
        f"- Longitude: {config.longitude if config.longitude is not None else 'Not set'}",
        f"- MeshCore channel: {config.meshcore_channel or '#weather-alerts'}",
        f"- Check interval: {config.poll_interval_seconds} seconds",
        f"- Repeat interval: {config.repeat_interval_minutes} minutes",
        f"- Logging level: {config.logging_level or 'INFO'}",
        "- Tracked locations:",
    ]

    if config.tracked_locations:
        for location in config.tracked_locations:
            if isinstance(location, dict):
                name = location.get("name", "Unnamed")
                state = location.get("state", "").strip() or "Unknown state"
                county = location.get("county", "").strip()
                details = f"{name} ({state})"
                if county:
                    details = f"{details} - {county}"
                lines.append(f"  - {details}")
            else:
                lines.append(f"  - {location}")
    else:
        lines.append("  - None")

    lines.append("- Alert types:")

    if config.alert_types:
        for alert_type in config.alert_types:
            lines.append(f"  - {alert_type}")
    else:
        lines.append("  - None")

    return "\n".join(lines)


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
        meshcore_channel=str(meshcore.get("channel", "#weather-alerts")),
        logging_level=str(logging_.get("level", "INFO")),
    )
