"""Command line interface for MeshCore Weather Gateway."""

from __future__ import annotations

import argparse
import subprocess
import sys
import threading
from pathlib import Path

from rich.console import Console

from meshcore_weather.config import load_config
from meshcore_weather.gateway import run_gateway, run_test_mode
from meshcore_weather.setup_wizard import run_setup
from meshcore_weather.version import __version__

console = Console()


def get_service_unit_path() -> Path:
    """Return the packaged systemd service unit path."""
    package_root = Path(__file__).resolve().parent
    candidate_paths = [
        package_root / "systemd" / "meshcore-weather.service",
        package_root.parent / "systemd" / "meshcore-weather.service",
    ]
    for candidate in candidate_paths:
        if candidate.exists():
            return candidate
    return candidate_paths[0]


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
        choices=["run", "stop", "install", "enable", "start", "status", "quick-start", "test", "validate"],
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

    if args.command == "install":
        try:
            service_path = Path("/etc/systemd/system/meshcore-weather.service")
            service_file = get_service_unit_path()
            if not service_file.exists():
                console.print("[red]Service unit file not found.[/red]")
                return
            service_path.write_text(service_file.read_text(encoding="utf-8"), encoding="utf-8")
            console.print(f"[green]Installed service unit to {service_path}[/green]")
        except Exception as exc:
            console.print(f"[red]Unable to install service: {exc}[/red]")
        return

    if args.command == "enable":
        try:
            subprocess.run(["systemctl", "enable", "meshcore-weather"], check=True)
            console.print("[green]Enabled meshcore-weather service.[/green]")
        except Exception as exc:
            console.print(f"[red]Unable to enable service: {exc}[/red]")
        return

    if args.command == "start":
        try:
            subprocess.run(["systemctl", "start", "meshcore-weather"], check=True)
            console.print("[green]Started meshcore-weather service.[/green]")
        except Exception as exc:
            console.print(f"[red]Unable to start service: {exc}[/red]")
        return

    if args.command == "stop":
        try:
            subprocess.run(["systemctl", "stop", "meshcore-weather"], check=True)
            console.print("[green]Stopped meshcore-weather service.[/green]")
        except Exception as exc:
            console.print(f"[red]Unable to stop service: {exc}[/red]")
        return

    if args.command == "status":
        try:
            subprocess.run(["systemctl", "status", "meshcore-weather"], check=True)
        except subprocess.CalledProcessError as exc:
            raise SystemExit(exc.returncode) from exc
        except Exception as exc:
            console.print(f"[red]Unable to show service status: {exc}[/red]")
        return

    if args.command == "quick-start":
        try:
            should_run_setup = not config_path.exists()
            if not should_run_setup:
                config = load_config(config_path)
                should_run_setup = not config.serial_port.strip() or config.latitude is None or config.longitude is None

            if should_run_setup:
                run_setup(config_path)

            for subcommand in ["install", "enable", "start"]:
                if subcommand == "install":
                    subprocess.run([sys.executable, "-m", "meshcore_weather.cli", "install", "--config", str(config_path)], check=True)
                else:
                    subprocess.run([sys.executable, "-m", "meshcore_weather.cli", subcommand, "--config", str(config_path)], check=True)
            console.print("[green]Quick start completed.[/green]")
        except Exception as exc:
            console.print(f"[red]Quick start failed: {exc}[/red]")
        return

    if args.command == "test":
        run_test_mode(config_path)
        return

    console.print(f"[bold cyan]MeshCore Weather Gateway[/bold cyan]")
    console.print(f"Version: [green]{__version__}[/green]")
    console.print()
    console.print("Use --help to see available commands.")
