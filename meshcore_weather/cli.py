"""Command line interface for MeshCore Weather Gateway."""

from __future__ import annotations

import argparse
import threading
import time
from pathlib import Path

from rich.console import Console

from meshcore_weather.broadcast import format_alert_message, send_message
from meshcore_weather.config import GatewayConfig, load_config, save_config
from meshcore_weather.dedupe import AlertTracker
from meshcore_weather.nws import Alert, build_alerts, fetch_active_alerts, fetch_weather_observation, filter_alerts
from meshcore_weather.setup_wizard import run_setup
from meshcore_weather.version import __version__

console = Console()


def run_gateway(config_path: Path | str | None = None, stop_event: threading.Event | None = None) -> None:
    """Run the gateway loop until interrupted or explicitly stopped."""
    destination = Path(config_path) if config_path is not None else Path("config.yaml")
    config = load_config(destination)
    errors = config.validate()

    if errors:
        console.print("[red]Configuration is invalid:[/red]")
        for error in errors:
            console.print(f"- {error}")
        return

    stop = stop_event or threading.Event()
    tracker = AlertTracker()
    console.print("[green]Gateway starting.[/green]")

    while not stop.is_set():
        console.print("[cyan]Checking for weather alerts...[/cyan]")
        payload = fetch_active_alerts()
        alerts = build_alerts(payload)
        filtered = filter_alerts(alerts, config)

        for alert in filtered:
            if not tracker.should_broadcast(alert.id):
                continue

            message = format_alert_message(
                event=alert.event,
                location=alert.area_desc,
                expires=alert.expires,
                description=alert.description,
            )
            sent = send_message(config.serial_port, message, channel=config.meshcore_channel)
            if sent:
                console.print(f"[magenta]Broadcasting:[/magenta] {message}")
            else:
                console.print(f"[yellow]Unable to broadcast alert {alert.id}[/yellow]")

        time.sleep(config.poll_interval_seconds)

    console.print("[yellow]Gateway stopped.[/yellow]")


def run_test_mode(config_path: Path | str | None = None) -> bool:
    """Fetch active NWS alerts, choose one to broadcast, and send it over the configured MeshCore channel."""
    destination = Path(config_path) if config_path is not None else Path("config.yaml")
    config = load_config(destination)
    errors = config.validate()

    if errors:
        console.print("[red]Configuration is invalid:[/red]")
        for error in errors:
            console.print(f"- {error}")
        return False

    payload = fetch_active_alerts()
    alerts = build_alerts(payload)
    filtered = filter_alerts(alerts, config)

    if filtered:
        alert = filtered[0]
        message = format_alert_message(
            event=alert.event,
            location=alert.area_desc,
            expires=alert.expires,
            description=alert.description,
        )
        console.print(f"[cyan]Sending alert to {config.meshcore_channel}[/cyan]")
        console.print(f"[cyan]{alert.event} - {alert.area_desc}[/cyan]")
        sent = send_message(config.serial_port, message, channel=config.meshcore_channel)
        if sent:
            console.print("[green]Alert sent successfully.[/green]")
        else:
            console.print("[yellow]Alert could not be sent.[/yellow]")
            console.print("[yellow]The MeshCore device may be disconnected, unavailable, or not reachable on the configured serial port.[/yellow]")
        return sent

    location = ""
    if config.tracked_locations:
        location = str(config.tracked_locations[0].get("county", "")).strip()
    if config.state and location:
        location = f"{config.state.lower()}/{location.lower()}"
    observation = fetch_weather_observation(location)

    if observation is None:
        console.print("[yellow]No matching alerts or observation data were found from the NWS feed.[/yellow]")
        return False

    parts = []
    if observation.temperature_f is not None:
        parts.append(f"Temp: {observation.temperature_f:.1f}F")
    if observation.humidity_percent is not None:
        parts.append(f"Humidity: {observation.humidity_percent:.0f}%")

    message = "Current weather: " + ", ".join(parts) if parts else "Current weather: unavailable"
    console.print(f"[cyan]Sending current weather to {config.meshcore_channel}[/cyan]")
    sent = send_message(config.serial_port, message, channel=config.meshcore_channel)
    if sent:
        console.print("[green]Current weather sent successfully.[/green]")
    else:
        console.print("[yellow]Current weather could not be sent.[/yellow]")
        console.print("[yellow]The MeshCore device may be disconnected, unavailable, or not reachable on the configured serial port.[/yellow]")

    return sent


def main() -> None:
    """Main CLI entry point."""

    parser = argparse.ArgumentParser(
        prog="meshcore-weather",
        description="MeshCore Weather Gateway",
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    parser.add_argument(
        "--setup",
        action="store_true",
        help="Run the interactive setup wizard.",
    )

    parser.add_argument(
        "--config",
        default="config.yaml",
        help="Path to the YAML configuration file.",
    )

    parser.add_argument(
        "command",
        nargs="?",
        choices=["run", "test", "validate"],
        help="Command to execute.",
    )

    args = parser.parse_args()

    config_path = Path(args.config)

    if args.setup:
        try:
            run_setup(config_path)
        except ValueError as exc:
            console.print(f"[red]{exc}[/red]")
        return

    if args.command == "validate":
        config = load_config(config_path)
        errors = config.validate()
        if errors:
            console.print("[red]Configuration is invalid:[/red]")
            for error in errors:
                console.print(f"- {error}")
            return

        console.print("[green]Configuration is valid.[/green]")
        return

    if args.command == "run":
        try:
            run_gateway(config_path)
        except KeyboardInterrupt:
            console.print("[yellow]Gateway interrupted.[/yellow]")
        return

    if args.command == "test":
        run_test_mode(config_path)
        return

    console.print(f"[bold cyan]MeshCore Weather Gateway[/bold cyan]")
    console.print(f"Version: [green]{__version__}[/green]")
    console.print()
    console.print("Use --help to see available commands.")
