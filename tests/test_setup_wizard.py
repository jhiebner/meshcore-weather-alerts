from meshcore_weather.config import GatewayConfig
from meshcore_weather.setup_wizard import build_configuration_summary


def test_configuration_summary_includes_key_values() -> None:
    config = GatewayConfig(
        serial_port="/dev/ttyUSB0",
        state="NE",
        tracked_locations=[{"county": "York", "nws_zone": "NEC185"}],
        alert_types=["Tornado Warning", "Severe Thunderstorm Warning"],
        poll_interval_seconds=60,
        repeat_interval_minutes=15,
    )

    summary = build_configuration_summary(config)

    assert "MeshCore serial port" in summary
    assert "/dev/ttyUSB0" in summary
    assert "York" in summary
    assert "Tornado Warning" in summary
