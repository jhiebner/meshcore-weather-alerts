"""Interactive setup wizard for the MeshCore Weather Gateway."""

from __future__ import annotations

from pathlib import Path

from rich.console import Console
from rich.prompt import Confirm, IntPrompt, Prompt

from meshcore_weather.config import GatewayConfig, save_config
from meshcore_weather.constants import DEFAULT_ALERT_TYPES
from meshcore_weather.validators import (
    normalize_county,
    normalize_state,
    parse_alert_types,
    validate_poll_interval,
    validate_repeat_interval,
)

console = Console()


def build_configuration_summary(config: GatewayConfig) -> str:
    """Create a short human-friendly summary of the configuration."""
    lines = [
        "Configuration summary",
        f"- MeshCore serial port: {config.serial_port or 'Not set'}",
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
            f"- Check interval: {config.poll_interval_seconds} seconds",
            f"- Repeat interval: {config.repeat_interval_minutes} minutes",
        ]
    )
    return "\n".join(lines)


def run_setup(config_path: str | Path | None = None) -> GatewayConfig:
    """Run the interactive setup wizard."""
    destination = Path(config_path) if config_path is not None else Path("config.yaml")

    console.print("[bold cyan]MeshCore Weather Gateway[/bold cyan]")
    console.print("[bold]Setup Wizard[/bold]")
    console.print()
    console.print("This wizard will guide you through a simple setup for your weather gateway.")
    console.print("You can press Enter to accept the suggested default values.")
    console.print()

    serial_port = Prompt.ask(
        "MeshCore serial port",
        default="/dev/ttyUSB0",
        show_default=True,
    ).strip()

    state = normalize_state(
        Prompt.ask("State code (for example NE)", default="NE")
    )

    county_inputs: list[str] = []
    for index in range(1, 4):
        value = Prompt.ask(
            f"County {index} (leave blank to skip)",
            default="",
            show_default=False,
        ).strip()
        if value:
            county_inputs.append(normalize_county(value))

    alert_type_choices = []
    while not alert_type_choices:
        raw = Prompt.ask(
            "Alert types (comma-separated numbers, e.g. 1,2,3)",
            default=",".join(
                str(index) for index, _ in enumerate(DEFAULT_ALERT_TYPES, start=1)
            ),
        )
        try:
            alert_type_choices = parse_alert_types(raw)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
            console.print("Please enter numbers such as 1,2,3.")

    poll_interval = validate_poll_interval(
        IntPrompt.ask("Check for alerts every how many seconds?", default=60)
    )
    repeat_interval = validate_repeat_interval(
        IntPrompt.ask("Repeat active alerts every how many minutes?", default=15)
    )

    config = GatewayConfig(
        serial_port=serial_port,
        state=state,
        tracked_locations=[{"county": county, "nws_zone": ""} for county in county_inputs],
        alert_types=alert_type_choices,
        poll_interval_seconds=poll_interval,
        repeat_interval_minutes=repeat_interval,
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
