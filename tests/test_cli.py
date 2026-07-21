import threading
from pathlib import Path

from meshcore_weather.cli import PID_FILE, get_service_unit_path, main, run_gateway


def test_run_gateway_exits_when_stop_event_is_set(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("meshcore:\n  serial_port: /dev/ttyUSB0\n", encoding="utf-8")

    stop_event = threading.Event()
    stop_event.set()

    run_gateway(config_path, stop_event=stop_event)


def test_service_command_updates_pid_file(tmp_path: Path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("meshcore:\n  serial_port: /dev/ttyUSB0\n", encoding="utf-8")

    monkeypatch.setattr("meshcore_weather.cli.PID_FILE", tmp_path / "meshcore-weather.pid")
    monkeypatch.setattr("meshcore_weather.cli.subprocess.Popen", lambda *args, **kwargs: type("Proc", (), {"pid": 4242})())

    monkeypatch.setattr("sys.argv", ["meshcore-weather", "service", "--config", str(config_path)])
    main()
    assert (tmp_path / "meshcore-weather.pid").read_text(encoding="utf-8") == "4242"


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
    monkeypatch.setattr("sys.argv", ["meshcore-weather", "enable", "--config", str(config_path)])
    main()
    assert calls == [["systemctl", "enable", "meshcore-weather"]]

    monkeypatch.setattr("sys.argv", ["meshcore-weather", "start", "--config", str(config_path)])
    main()
    assert calls[-1] == ["systemctl", "start", "meshcore-weather"]

    monkeypatch.setattr("sys.argv", ["meshcore-weather", "stop", "--config", str(config_path)])
    main()
    assert calls[-1] == ["systemctl", "stop", "meshcore-weather"]
