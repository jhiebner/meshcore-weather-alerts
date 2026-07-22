"""Command line interface for MeshCore Weather Gateway."""

from __future__ import annotations

import argparse
import os
import shutil
import subprocess
import sys
import tempfile
import threading
from pathlib import Path

from rich.console import Console

from meshcore_weather.config import load_config
from meshcore_weather.gateway import run_gateway, run_test_mode
from meshcore_weather.setup_wizard import run_setup
from meshcore_weather.version import __version__

console = Console()


def run_systemctl(action: str) -> None:
    command = ["systemctl", action, "meshcore-weather"]
    if os.geteuid() != 0:
        command = ["sudo", *command]
    subprocess.run(command, check=True)


def is_systemd_service_active() -> bool:
    command = ["systemctl", "is-active", "--quiet", "meshcore-weather"]
    if os.geteuid() != 0:
        command = ["sudo", *command]
    return subprocess.run(command, check=False).returncode == 0


def get_systemd_service_status() -> str:
    command = ["systemctl", "status", "meshcore-weather"]
    if os.geteuid() != 0:
        command = ["sudo", *command]

    result = subprocess.run(command, check=False, capture_output=True, text=True)
    output = (result.stdout or "").strip()
    error_output = (result.stderr or "").strip()
    if output and error_output:
        return f"{output}\n{error_output}"
    return output or error_output or "No status output available."


def reload_systemd_daemon() -> None:
    command = ["systemctl", "daemon-reload"]
    if os.geteuid() != 0:
        command = ["sudo", *command]
    subprocess.run(command, check=True)


def resolve_system_meshcore_executable() -> str:
    """Return an absolute meshcore-weather executable path outside virtual environments."""
    preferred_paths = [
        "/usr/local/bin/meshcore-weather",
        "/usr/bin/meshcore-weather",
    ]
    for candidate in preferred_paths:
        candidate_path = Path(candidate)
        if candidate_path.exists() and os.access(candidate_path, os.X_OK):
            return str(candidate_path)

    discovered = shutil.which("meshcore-weather")
    if not discovered:
        raise RuntimeError(
            "meshcore-weather command not found on system PATH. Install it system-wide before running install/quick-start."
        )

    virtual_env = os.environ.get("VIRTUAL_ENV", "")
    in_virtual_env = "/.venv/" in discovered or (virtual_env and discovered.startswith(virtual_env))
    if in_virtual_env:
        raise RuntimeError(
            "meshcore-weather was found only inside a virtual environment. Install it system-wide so systemd can run it outside the venv."
        )

    return discovered


def build_service_unit_contents(service_file: Path, exec_path: str, config_path: Path) -> str:
    """Return service unit text with an absolute ExecStart for systemd."""
    lines = service_file.read_text(encoding="utf-8").splitlines()
    rendered = []
    for line in lines:
        if line.startswith("ExecStart="):
            rendered.append(f"ExecStart={exec_path} run --config {config_path}")
        else:
            rendered.append(line)
    return "\n".join(rendered) + "\n"


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
            runtime_dir = Path("/opt/meshcore-weather")
            runtime_config_path = runtime_dir / "config.yaml"
            service_file = get_service_unit_path()
            exec_path = resolve_system_meshcore_executable()
            if not service_file.exists():
                console.print("[red]Service unit file not found.[/red]")
                return
            rendered_unit = build_service_unit_contents(service_file, exec_path, runtime_config_path)
            if os.geteuid() == 0:
                runtime_dir.mkdir(parents=True, exist_ok=True)
                if config_path.exists():
                    runtime_config_path.write_text(config_path.read_text(encoding="utf-8"), encoding="utf-8")
                service_path.write_text(rendered_unit, encoding="utf-8")
            else:
                subprocess.run(["sudo", "install", "-d", "/opt/meshcore-weather"], check=True)
                if config_path.exists():
                    subprocess.run(["sudo", "install", "-Dm644", str(config_path), str(runtime_config_path)], check=True)
                with tempfile.NamedTemporaryFile("w", encoding="utf-8", delete=False) as handle:
                    handle.write(rendered_unit)
                    temp_unit_path = Path(handle.name)
                try:
                    subprocess.run(["sudo", "install", "-Dm644", str(temp_unit_path), str(service_path)], check=True)
                finally:
                    temp_unit_path.unlink(missing_ok=True)
            reload_systemd_daemon()
            console.print(f"[green]Installed service unit to {service_path}[/green]")
        except Exception as exc:
            console.print(f"[red]Unable to install service: {exc}[/red]")
        return

    if args.command == "enable":
        try:
            run_systemctl("enable")
            console.print("[green]Enabled meshcore-weather service.[/green]")
        except Exception as exc:
            console.print(f"[red]Unable to enable service: {exc}[/red]")
        return

    if args.command == "start":
        try:
            run_systemctl("start")
            console.print("[green]Started meshcore-weather service.[/green]")
        except Exception as exc:
            console.print(f"[red]Unable to start service: {exc}[/red]")
        return

    if args.command == "stop":
        try:
            run_systemctl("stop")
            console.print("[green]Stopped meshcore-weather service.[/green]")
        except Exception as exc:
            console.print(f"[red]Unable to stop service: {exc}[/red]")
        return

    if args.command == "status":
        try:
            run_systemctl("status")
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

            if not is_systemd_service_active():
                raise RuntimeError(
                    "meshcore-weather.service did not become active after start\n"
                    f"{get_systemd_service_status()}"
                )

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
