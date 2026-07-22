from meshcore_weather.broadcast import (
    MAX_MESHCORE_MESSAGE_LENGTH,
    format_alert_message,
    send_message,
    split_message_chunks,
)


class StubTransport:
    def __init__(self) -> None:
        self.calls: list[tuple[str, str, str | None]] = []

    def send(self, serial_port: str, message: str, channel: str | None = None) -> bool:
        self.calls.append((serial_port, message, channel))
        return True


class FailingChunkTransport:
    def __init__(self, fail_on_call: int) -> None:
        self.calls: list[tuple[str, str, str | None]] = []
        self.fail_on_call = fail_on_call

    def send(self, serial_port: str, message: str, channel: str | None = None) -> bool:
        self.calls.append((serial_port, message, channel))
        return len(self.calls) != self.fail_on_call


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


def test_split_message_chunks_enforces_142_char_limit() -> None:
    message = "A" * 400
    chunks = split_message_chunks(message)

    assert len(chunks) == 3
    assert all(len(chunk) <= MAX_MESHCORE_MESSAGE_LENGTH for chunk in chunks)


def test_send_message_splits_long_message_for_transport() -> None:
    transport = StubTransport()
    message = "A" * 400

    result = send_message("/dev/ttyUSB0", message, transport=transport)

    assert result is True
    assert len(transport.calls) == 3
    assert all(len(sent_message) <= MAX_MESHCORE_MESSAGE_LENGTH for _, sent_message, _ in transport.calls)


def test_send_message_returns_false_when_any_chunk_fails() -> None:
    transport = FailingChunkTransport(fail_on_call=2)
    message = "A" * 400

    result = send_message("/dev/ttyUSB0", message, transport=transport)

    assert result is False
    assert len(transport.calls) == 2
