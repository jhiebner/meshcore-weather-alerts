from meshcore_weather.config import GatewayConfig
from meshcore_weather.constants import SUPPORTED_ALERT_TYPES
from meshcore_weather.setup_wizard import (
    build_configuration_summary,
    build_setup_defaults,
    get_alert_type_choices,
)


def test_configuration_summary_includes_key_values() -> None:
    config = GatewayConfig(
        serial_port="/dev/ttyUSB0",
        latitude=40.7,
        longitude=-74.0,
        alert_types=["Tornado Warning", "Severe Thunderstorm Warning"],
        poll_interval_seconds=60,
        repeat_interval_minutes=15,
    )

    summary = build_configuration_summary(config)

    assert "MeshCore serial port" in summary
    assert "/dev/ttyUSB0" in summary
    assert "40.7" in summary
    assert "Tornado Warning" in summary


def test_build_setup_defaults_uses_existing_config_values() -> None:
    config = GatewayConfig(
        serial_port="/dev/ttyUSB1",
        latitude=41.6,
        longitude=-93.6,
        alert_types=["Tornado Warning"],
        poll_interval_seconds=120,
        repeat_interval_minutes=30,
        meshcore_channel="#alerts",
    )

    defaults = build_setup_defaults(config)

    assert defaults["serial_port"] == "/dev/ttyUSB1"
    assert defaults["latitude"] == 41.6
    assert defaults["longitude"] == -93.6
    assert defaults["alert_type_choices"] == ["Tornado Warning"]
    assert defaults["meshcore_channel"] == "#alerts"
    assert defaults["poll_interval"] == 120
    assert defaults["repeat_interval"] == 30


def test_alert_type_choices_use_full_supported_list() -> None:
    assert get_alert_type_choices() == SUPPORTED_ALERT_TYPES
