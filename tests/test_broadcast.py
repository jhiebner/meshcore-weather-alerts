from meshcore_weather.broadcast import format_alert_message, send_message


class StubTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []

    def send(self, serial_port: str, message: str, channel: str | None = None) -> bool:
        self.calls.append((serial_port, message, channel))
        return True


def test_format_alert_message_is_compact_and_readable() -> None:
    message = format_alert_message(
        event="Tornado Warning",
        location="York County",
        expires="2026-07-13T02:00:00+00:00",
        description="Take shelter immediately.",
    )

    assert "TORNADO WARNING" in message
    assert "York County" in message
    assert "Take shelter immediately." in message


def test_send_message_returns_success_for_mock_transport() -> None:
    result = send_message("/dev/ttyUSB0", "Test message")

    assert result is False


def test_send_message_uses_channel_when_transport_provides_one() -> None:
    transport = StubTransport()

    result = send_message(
        "/dev/ttyUSB0",
        "Test message",
        transport=transport,
    )

    assert result is True
    assert transport.calls == [("/dev/ttyUSB0", "Test message", None)]
