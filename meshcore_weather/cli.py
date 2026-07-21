"""Command line interface for MeshCore Weather Gateway."""

from __future__ import annotations

import argparse
import threading
from pathlib import Path

from rich.console import Console

from meshcore_weather.config import load_config
from meshcore_weather.gateway import run_gateway, run_test_mode
from meshcore_weather.setup_wizard import run_setup
from meshcore_weather.version import __version__

console = Console()


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
