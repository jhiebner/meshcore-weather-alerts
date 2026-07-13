"""MeshCore client integration for sending weather alerts."""

from __future__ import annotations

import asyncio
from typing import Any

from meshcore import MeshCore
from meshcore.commands import CommandHandler


class MeshCoreClient:
    """Simple wrapper around the meshcore Python package."""

    def __init__(self, serial_port: str, baudrate: int = 115200) -> None:
        self.serial_port = serial_port
        self.baudrate = baudrate
        self._client: MeshCore | None = None

    async def connect(self) -> bool:
        """Create and connect a MeshCore client using the serial port."""
        try:
            self._client = await MeshCore.create_serial(self.serial_port, baudrate=self.baudrate)
        except Exception:
            self._client = None
            return False
        return self._client is not None

    async def disconnect(self) -> None:
        """Disconnect the MeshCore client if it exists."""
        if self._client is not None:
            await self._client.disconnect()
            self._client = None

    async def send_message(self, message: str) -> bool:
        """Send a text message using the MeshCore command handler."""
        if self._client is None:
            return False

        command_handler: CommandHandler = self._client.commands
        payload = message.encode("utf-8")
        event = await command_handler.send(payload, expected_events=None)
        return bool(event)
