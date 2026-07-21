"""Gateway runtime orchestration for the MeshCore weather broadcaster."""

from __future__ import annotations

import threading
import time
from pathlib import Path

from rich.console import Console

from meshcore_weather.broadcast import format_alert_message, send_message
from meshcore_weather.config import load_config
from meshcore_weather.dedupe import AlertTracker
from meshcore_weather.nws import (
    build_alerts,
    build_forecast_message,
    fetch_active_alerts,
    fetch_forecast,
    fetch_location_zones,
    filter_alerts,
)

console = Console()


def _build_location(config) -> str:
    """Build the coordinates string used for NWS lookups."""
    if config.latitude is None or config.longitude is None:
        return ""
    return f"{config.latitude},{config.longitude}"


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
        location = _build_location(config)
        filtered = filter_alerts(alerts, config, location_zones=fetch_location_zones(location))

        for alert in filtered:
            if not tracker.should_broadcast(alert.id, repeat_interval_minutes=config.repeat_interval_minutes):
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
    """Fetch active NWS alerts, choose one to broadcast, or fall back to the forecast."""
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
    location = _build_location(config)
    filtered = filter_alerts(alerts, config, location_zones=fetch_location_zones(location))

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

    forecast = fetch_forecast(location)
    if not forecast:
        console.print("[yellow]No forecast data was found from the NWS feed.[/yellow]")
        return False

    message = build_forecast_message({"properties": {"periods": [period.__dict__ for period in forecast]}})
    console.print(f"[cyan]Sending forecast to {config.meshcore_channel}[/cyan]")
    sent = send_message(config.serial_port, message, channel=config.meshcore_channel)
    if sent:
        console.print("[green]Forecast sent successfully.[/green]")
    else:
        console.print("[yellow]Forecast could not be sent.[/yellow]")
        console.print("[yellow]The MeshCore device may be disconnected, unavailable, or not reachable on the configured serial port.[/yellow]")

    return sent
