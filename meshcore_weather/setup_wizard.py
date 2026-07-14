"""Interactive setup wizard for the MeshCore Weather Gateway."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from meshcore_weather.config import GatewayConfig, save_config
from meshcore_weather.constants import DEFAULT_ALERT_TYPES
from meshcore_weather.validators import (
    normalize_state,
    parse_alert_types,
    validate_latitude,
    validate_longitude,
    validate_poll_interval,
    validate_repeat_interval,
)

console = Console()


def build_configuration_summary(config: GatewayConfig) -> str:
    """Create a short human-friendly summary of the configuration."""
    lines = [
        "Configuration summary",
        f"- MeshCore serial port: {config.serial_port or 'Not set'}",
        f"- Latitude: {config.latitude if config.latitude is not None else 'Not set'}",
        f"- Longitude: {config.longitude if config.longitude is not None else 'Not set'}",
        f"- State: {config.state or 'Not set'}",
        "- Counties:",
    ]

    if config.tracked_locations:
        for location in config.tracked_locations:
            county = location.get("county", "")
            lines.append(f"  - {county}")
    else:
        lines.append("  - None")

    lines.extend(
        [
            "- Alert types:",
        ]
    )

    if config.alert_types:
        for alert_type in config.alert_types:
            lines.append(f"  - {alert_type}")
    else:
        lines.append("  - None")

    lines.extend(
        [
            f"- MeshCore channel: {config.meshcore_channel or '#weather-alert'}",
            f"- Check interval: {config.poll_interval_seconds} seconds",
            f"- Repeat interval: {config.repeat_interval_minutes} minutes",
        ]
    )
    return "\n".join(lines)


def build_setup_defaults(existing_config: GatewayConfig | None = None) -> dict[str, object]:
    """Return prompt defaults based on any existing saved configuration."""
    config = existing_config or GatewayConfig()
    return {
        "serial_port": config.serial_port or "/dev/ttyUSB0",
        "latitude": config.latitude,
        "longitude": config.longitude,
        "state": config.state,
        "county_inputs": [location.get("county", "") for location in config.tracked_locations if location.get("county")],
        "alert_type_choices": list(config.alert_types),
        "meshcore_channel": config.meshcore_channel or "#weather-alert",
        "poll_interval": config.poll_interval_seconds,
        "repeat_interval": config.repeat_interval_minutes,
    }


def run_setup(config_path: str | Path | None = None) -> GatewayConfig:
    """Run the interactive setup wizard."""
    destination = Path(config_path) if config_path is not None else Path("config.yaml")
    existing_config = GatewayConfig()
    if destination.exists():
        existing_config = GatewayConfig(
            serial_port="",
            state="",
            tracked_locations=[],
            alert_types=[],
            poll_interval_seconds=60,
            repeat_interval_minutes=15,
            meshcore_channel="#weather-alert",
        )
        try:
            from meshcore_weather.config import load_config

            existing_config = load_config(destination)
        except Exception:
            existing_config = GatewayConfig()

    defaults = build_setup_defaults(existing_config)

    console.print("[bold cyan]MeshCore Weather Gateway[/bold cyan]")
    console.print("[bold]Setup Wizard[/bold]")
    console.print()
    console.print("This wizard will guide you through a simple setup for your weather gateway.")
    console.print("You can press Enter to accept the suggested default values.")
    console.print()

    serial_port = Prompt.ask(
        "MeshCore serial port",
        default=str(defaults["serial_port"]),
        show_default=True,
    ).strip()

    latitude_value = validate_latitude(
        Prompt.ask(
            "Latitude",
            default=str(defaults["latitude"]) if defaults["latitude"] is not None else "",
        )
    )
    longitude_value = validate_longitude(
        Prompt.ask(
            "Longitude",
            default=str(defaults["longitude"]) if defaults["longitude"] is not None else "",
        )
    )

    state = normalize_state(
        Prompt.ask("State code (for example NE)", default=str(defaults["state"] or ""))
    )

    county_inputs: list[str] = []
    existing_counties = list(defaults["county_inputs"])  # type: ignore[arg-type]
    for index in range(1, 4):
        county_default = existing_counties[index - 1] if index - 1 < len(existing_counties) else ""
        value = Prompt.ask(
            f"County {index} (leave blank to skip)",
            default=county_default,
            show_default=False,
        ).strip()
        if value:
            county_inputs.append(value)

    alert_type_choices = []
    existing_alert_types = list(defaults["alert_type_choices"])  # type: ignore[arg-type]
    while not alert_type_choices:
        console.print("Select alert types to broadcast:")
        for index, alert_type in enumerate(DEFAULT_ALERT_TYPES, start=1):
            console.print(f"  {index}. {alert_type}")
        default_alerts = ",".join(
            str(index)
            for index, alert_type in enumerate(DEFAULT_ALERT_TYPES, start=1)
            if alert_type in existing_alert_types
        ) or ",".join(
            str(index) for index, _ in enumerate(DEFAULT_ALERT_TYPES, start=1)
        )
        raw = Prompt.ask(
            "Enter numbers separated by commas (for example 1,2,3)",
            default=default_alerts,
        )
        try:
            alert_type_choices = parse_alert_types(raw)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            console.print("Please enter numbers such as 1,2,3.")

    meshcore_channel = Prompt.ask(
        "MeshCore channel to send alerts to",
        default=str(defaults["meshcore_channel"]),
        show_default=True,
    ).strip() or "#weather-alert"

    poll_interval = validate_poll_interval(
        IntPrompt.ask(
            "Check for alerts every how many seconds?",
            default=int(defaults["poll_interval"]),
        )
    )
    repeat_interval = validate_repeat_interval(
        IntPrompt.ask(
            "Repeat active alerts every how many minutes?",
            default=int(defaults["repeat_interval"]),
        )
    )

    config = GatewayConfig(
        serial_port=serial_port,
        latitude=latitude_value,
        longitude=longitude_value,
        state=state,
        tracked_locations=[{"county": county, "nws_zone": ""} for county in county_inputs],
        alert_types=alert_type_choices,
        poll_interval_seconds=poll_interval,
        repeat_interval_minutes=repeat_interval,
        meshcore_channel=meshcore_channel,
    )

    console.print()
    console.print("[bold]Review your settings[/bold]")
    console.print(build_configuration_summary(config))
    console.print()

    errors = config.validate()
    if errors:
        console.print("[red]Configuration issues detected:[/red]")
        for error in errors:
            console.print(f"- {error}")
        if not Confirm.ask("Save anyway?", default=False):
            raise ValueError("setup cancelled")

    if not Confirm.ask("Save this configuration?", default=True):
        raise ValueError("setup cancelled")

    save_config(config, destination)
    console.print(f"[green]Configuration saved to {destination}[/green]")
    return config
