from meshcore_weather.cli import run_test_mode
from meshcore_weather.nws import Alert


def test_run_test_mode_uses_configured_channel(tmp_path) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "meshcore:\n  serial_port: /dev/ttyUSB0\n  channel: '#weather-alert'\n",
        encoding="utf-8",
    )

    result = run_test_mode(config_path)

    assert result is False


def test_run_test_mode_fetches_alerts_and_broadcasts_one(tmp_path, monkeypatch) -> None:
    config_path = tmp_path / "config.yaml"
    config_path.write_text(
        "meshcore:\n  serial_port: /dev/ttyUSB0\n  channel: '#weather-alert'\n"
        "weather:\n  latitude: 40.7\n  longitude: -74.0\n  state: NE\n  tracked_locations:\n    - county: York\n      nws_zone: NEC185\n"
        "  alert_types:\n    - Tornado Warning\n"
        "schedule:\n  poll_interval_seconds: 60\n  repeat_interval_minutes: 15\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(
        "meshcore_weather.cli.fetch_active_alerts",
        lambda: {"features": [{"id": "1", "properties": {"event": "Tornado Warning"}}]},
    )
    monkeypatch.setattr(
        "meshcore_weather.cli.build_alerts",
        lambda payload: [
            Alert(
                id="1",
                event="Tornado Warning",
                headline="Tornado Warning",
                description="Take shelter immediately.",
                instruction="",
                severity="Severe",
                sent="",
                expires="",
                sender_name="",
                area_desc="York County",
                zones=["NEC185"],
            )
        ],
    )
    monkeypatch.setattr("meshcore_weather.cli.filter_alerts", lambda alerts, config: alerts)

    captured: dict[str, object] = {}

    def fake_send_message(serial_port: str, message: str, channel: str | None = None) -> bool:
        captured["serial_port"] = serial_port
        captured["message"] = message
        captured["channel"] = channel
        return True

    monkeypatch.setattr("meshcore_weather.cli.send_message", fake_send_message)

    result = run_test_mode(config_path)

    assert result is True
    assert captured["channel"] == "#weather-alert"
    assert "TORNADO WARNING" in str(captured["message"]).upper()
