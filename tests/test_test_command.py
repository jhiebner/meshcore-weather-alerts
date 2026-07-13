from meshcore_weather.cli import run_test_mode


def test_run_test_mode_uses_configured_channel(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "meshcore:\n  serial_port: /dev/ttyUSB0\n  channel: '#weather-alert'\n",
        encoding="utf-8",
    )

    result = run_test_mode(config_path)

    assert result is False
