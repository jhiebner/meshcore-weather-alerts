import threading
from pathlib import Path

from meshcore_weather.cli import run_gateway


def test_run_gateway_exits_when_stop_event_is_set(tmp_path: Path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text("meshcore:\n  serial_port: /dev/ttyUSB0\n", encoding="utf-8")

    stop_event = threading.Event()
    stop_event.set()

    run_gateway(config_path, stop_event=stop_event)
