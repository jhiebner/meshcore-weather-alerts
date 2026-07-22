"""Broadcasting helpers for sending weather alerts over MeshCore."""

from __future__ import annotations

import asyncio
from typing import Any

from meshcore_weather.meshcore_client import MeshCoreClient

MAX_MESHCORE_MESSAGE_LENGTH = 142


def format_alert_message(event: str, location: str, expires: str, description: str) -> str:
    """Create a compact alert message suitable for MeshCore broadcast."""
    return (
        "⚠ ALERT\n"
        f"{event.upper()}\n"
        f"{location}\n"
        f"Expires: {expires}\n"
        f"{description}"
    )


def split_message_chunks(message: str, max_length: int = MAX_MESHCORE_MESSAGE_LENGTH) -> list[str]:
    """Split long messages into <= max_length character chunks."""
    if max_length <= 0:
        raise ValueError("max_length must be greater than zero")

    if len(message) <= max_length:
        return [message]

    chunks: list[str] = []
    remaining = message

    while len(remaining) > max_length:
        split_at = remaining.rfind(" ", 0, max_length + 1)
        if split_at <= 0:
            split_at = max_length

        chunk = remaining[:split_at].rstrip()
        if not chunk:
            chunk = remaining[:max_length]
            split_at = max_length

        chunks.append(chunk)
        remaining = remaining[split_at:].lstrip()

    if remaining:
        chunks.append(remaining)

    return chunks


def send_message(
    serial_port: str,
    message: str,
    transport: Any | None = None,
    channel: str | None = None,
) -> bool:
    """Send a message over MeshCore using the meshcore Python package."""
    chunks = split_message_chunks(message)

    if transport is None:
        client = MeshCoreClient(serial_port)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError("send_message must be run from a synchronous context")

        try:
            return asyncio.run(_send_with_client(client, chunks, channel))
        except RuntimeError:
            return False

    for chunk in chunks:
        if not transport.send(serial_port, chunk, channel=channel):
            return False
    return True


async def _send_with_client(client: MeshCoreClient, chunks: list[str], channel: str | None = None) -> bool:
    """Connect to the mesh node and send the message asynchronously."""
    connected = await client.connect()
    if not connected:
        return False

    try:
        for chunk in chunks:
            sent = await client.send_message(chunk, channel=channel)
            if not sent:
                return False
        return True
    finally:
        await client.disconnect()
