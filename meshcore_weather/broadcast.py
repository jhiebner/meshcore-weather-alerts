"""Broadcasting helpers for sending weather alerts over MeshCore."""

from __future__ import annotations

import asyncio
from typing import Any

from meshcore_weather.meshcore_client import MeshCoreClient


def format_alert_message(event: str, location: str, expires: str, description: str) -> str:
    """Create a compact alert message suitable for MeshCore broadcast."""
    return (
        "⚠ ALERT\n"
        f"{event.upper()}\n"
        f"{location}\n"
        f"Expires: {expires}\n"
        f"{description}"
    )


def send_message(serial_port: str, message: str, transport: Any | None = None) -> bool:
    """Send a message over MeshCore using the meshcore Python package."""
    if transport is None:
        client = MeshCoreClient(serial_port)
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            loop = None

        if loop and loop.is_running():
            raise RuntimeError("send_message must be run from a synchronous context")

        try:
            return asyncio.run(_send_with_client(client, message))
        except RuntimeError:
            return False

    return bool(transport.send(serial_port, message))


async def _send_with_client(client: MeshCoreClient, message: str) -> bool:
    """Connect to the mesh node and send the message asynchronously."""
    connected = await client.connect()
    if not connected:
        return False

    try:
        return await client.send_message(message)
    finally:
        await client.disconnect()
