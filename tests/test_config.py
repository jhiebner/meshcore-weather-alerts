from pathlib import Path

from meshcore_weather.config import GatewayConfig, load_config, save_config


def test_save_and_load_config(tmp_path: Path) -> None:
    config = GatewayConfig(
        serial_port="/dev/ttyUSB0",
        latitude=40.7,
        longitude=-74.0,
        state="NE",
        tracked_locations=[{"county": "York", "nws_zone": "NEC185"}],
        alert_types=["Tornado Warning"],
        poll_interval_seconds=60,
        repeat_interval_minutes=15,
        logging_level="INFO",
    )

    config_path = tmp_path / "config.yaml"
    save_config(config, config_path)

    loaded = load_config(config_path)

    assert loaded.serial_port == "/dev/ttyUSB0"
    assert loaded.latitude == 40.7
    assert loaded.longitude == -74.0
    assert loaded.state == "NE"
    assert loaded.tracked_locations[0]["county"] == "York"
    assert loaded.alert_types == ["Tornado Warning"]
    assert loaded.poll_interval_seconds == 60
    assert loaded.repeat_interval_minutes == 15
    assert loaded.logging_level == "INFO"


def test_validate_config_rejects_empty_serial_port(tmp_path: Path) -> None:
    config = GatewayConfig(
        serial_port="",
        latitude=40.7,
        longitude=-74.0,
        state="NE",
        tracked_locations=[],
        alert_types=["Tornado Warning"],
        poll_interval_seconds=60,
        repeat_interval_minutes=15,
        logging_level="INFO",
    )

    errors = config.validate()

    assert "serial_port" in errors
