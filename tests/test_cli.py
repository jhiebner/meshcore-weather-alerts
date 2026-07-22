import threading
from pathlib import Path

import pytest

from meshcore_weather.cli import (
    build_service_unit_contents,
    get_service_unit_path,
    main,
    resolve_system_meshcore_executable,
    run_gateway,
)


def test_run_gateway_exits_when_stop_event_is_set(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("meshcore:\n  serial_port: /dev/ttyUSB0\n", encoding="utf-8")

    stop_event = threading.Event()
    stop_event.set()

    run_gateway(config_path, stop_event=stop_event)


def test_service_unit_template_is_available() -> None:
    path = get_service_unit_path()
    assert path.exists()
    assert path.is_file()


def test_service_management_commands_call_systemctl(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("meshcore:\n  serial_port: /dev/ttyUSB0\n", encoding="utf-8")

    calls = []

    def fake_run(args, check=False):
        calls.append(args)
        return None

    monkeypatch.setattr("meshcore_weather.cli.subprocess.run", fake_run)
    monkeypatch.setattr("meshcore_weather.cli.os.geteuid", lambda: 1000)
    monkeypatch.setattr("sys.argv", ["meshcore-weather", "enable", "--config", str(config_path)])
    main()
    assert calls == [["sudo", "systemctl", "enable", "meshcore-weather"]]

    monkeypatch.setattr("sys.argv", ["meshcore-weather", "start", "--config", str(config_path)])
    main()
    assert calls[-1] == ["sudo", "systemctl", "start", "meshcore-weather"]

    monkeypatch.setattr("sys.argv", ["meshcore-weather", "stop", "--config", str(config_path)])
    main()
    assert calls[-1] == ["sudo", "systemctl", "stop", "meshcore-weather"]


def test_resolve_system_meshcore_executable_prefers_system_path(monkeypatch, tmp_path: Path) -> None:
    local_bin = tmp_path / "meshcore-weather"
    local_bin.write_text("#!/bin/sh\n", encoding="utf-8")
    local_bin.chmod(0o755)

    monkeypatch.setattr("meshcore_weather.cli.Path.exists", lambda p: str(p) == str(local_bin))
    monkeypatch.setattr("meshcore_weather.cli.os.access", lambda p, mode: str(p) == str(local_bin))
    monkeypatch.setattr("meshcore_weather.cli.shutil.which", lambda _: str(local_bin))

    result = resolve_system_meshcore_executable()
    assert result == str(local_bin)


def test_resolve_system_meshcore_executable_rejects_virtualenv_only(monkeypatch) -> None:
    monkeypatch.setattr("meshcore_weather.cli.Path.exists", lambda p: False)
    monkeypatch.setattr("meshcore_weather.cli.os.access", lambda p, mode: False)
    monkeypatch.setattr("meshcore_weather.cli.shutil.which", lambda _: "/tmp/project/.venv/bin/meshcore-weather")
    monkeypatch.setenv("VIRTUAL_ENV", "/tmp/project/.venv")

    with pytest.raises(RuntimeError, match="virtual environment"):
        resolve_system_meshcore_executable()


def test_build_service_unit_contents_replaces_execstart(tmp_path: Path) -> None:
    unit_file = tmp_path / "meshcore-weather.service"
    unit_file.write_text(
        "[Service]\n"
        "ExecStart=/usr/bin/env meshcore-weather run --config /opt/meshcore-weather/config.yaml\n",
        encoding="utf-8",
    )

    rendered = build_service_unit_contents(
        unit_file,
        "/usr/local/bin/meshcore-weather",
        Path("/opt/meshcore-weather/config.yaml"),
    )

    assert "ExecStart=/usr/local/bin/meshcore-weather run --config /opt/meshcore-weather/config.yaml" in rendered


def test_quick_start_reports_status_when_service_stays_inactive(monkeypatch, tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "meshcore:\n  serial_port: /dev/ttyUSB0\n  channel: '#weather-alert'\n"
        "weather:\n  latitude: 40.7\n  longitude: -74.0\n  alert_types:\n    - Tornado Warning\n"
        "schedule:\n  poll_interval_seconds: 60\n  repeat_interval_minutes: 15\n",
        encoding="utf-8",
    )

    prints = []

    def fake_print(message):
        prints.append(message)

    class Result:
        def __init__(self, returncode=0, stdout="", stderr=""):
            self.returncode = returncode
            self.stdout = stdout
            self.stderr = stderr

    def fake_run(args, check=False, capture_output=False, text=False):
        if args[:2] == ["sudo", "install"] or args[:2] == ["systemctl", "install"]:
            return Result()
        if args[:3] == ["sudo", "systemctl", "enable"] or args[:2] == ["systemctl", "enable"]:
            return Result()
        if args[:3] == ["sudo", "systemctl", "start"] or args[:2] == ["systemctl", "start"]:
            return Result()
        if args[:3] == ["sudo", "systemctl", "is-active"] or args[:2] == ["systemctl", "is-active"]:
            return Result(returncode=1)
        if args[:3] == ["sudo", "systemctl", "status"] or args[:2] == ["systemctl", "status"]:
            return Result(stdout="meshcore-weather.service - failed to start")
        return Result()

    monkeypatch.setattr("meshcore_weather.cli.subprocess.run", fake_run)
    monkeypatch.setattr("meshcore_weather.cli.os.geteuid", lambda: 1000)
    monkeypatch.setattr("meshcore_weather.cli.console.print", fake_print)
    monkeypatch.setattr("sys.argv", ["meshcore-weather", "quick-start", "--config", str(config_path)])
    main()

    assert any("Quick start failed" in str(message) for message in prints)
    assert any("meshcore-weather.service - failed to start" in str(message) for message in prints)
