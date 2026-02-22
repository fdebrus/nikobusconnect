"""
Nikobus Event Listener.
"""

from __future__ import annotations

import asyncio
import logging
import re
from typing import Any, Callable

from .protocol import calc_crc2, int_to_hex

_LOGGER = logging.getLogger(__name__)

class NikobusEventListener:
    """Listens to the PC-Link serial stream and dispatches decoded Nikobus frames."""

    def __init__(
        self,
        connection: Any,
        event_callback: Callable[[str], Any],
        feedback_callback: Optional[Callable[[int, str], Any]] = None,
    ) -> None:
        """
        Initialize the listener.
        
        Args:
            connection: The NikobusConnect instance.
            event_callback: Callback for general bus events (button presses, etc.).
            feedback_callback: Optional callback specifically for feedback module answers.
        """
        self._connection = connection
        self._event_callback = event_callback
        self._feedback_callback = feedback_callback

        self._running = False
        self._listener_task: asyncio.Task | None = None
        self.response_queue: asyncio.Queue[str] = asyncio.Queue()
        self._frame_buffer = ""
        self._module_group = 1

    async def start(self) -> None:
        """Start the background listening task."""
        self._running = True
        self._listener_task = asyncio.create_task(self._listen_loop())
        _LOGGER.info("Nikobus Event Listener started.")

    async def stop(self) -> None:
        """Stop the listener."""
        self._running = False
        if self._listener_task:
            self._listener_task.cancel()
            self._listener_task = None

    async def _listen_loop(self) -> None:
        """Continuous loop to read from the Nikobus connection."""
        while self._running:
            try:
                data = await asyncio.wait_for(self._connection.read(), timeout=10)
                if not data:
                    continue

                # Nikobus uses Windows-1252 encoding for bus communication
                raw_text = data.decode("Windows-1252", errors="ignore")
                for frame in self._extract_frames(raw_text):
                    _LOGGER.debug("Bus Frame: %s", frame)
                    await self._dispatch_message(frame)
            except asyncio.TimeoutError:
                continue
            except Exception as err:
                _LOGGER.error("Listener loop error: %s", err)
                await asyncio.sleep(1)

    def _extract_frames(self, raw: str) -> list[str]:
        """Normalize and extract frames from serial data using Platinum Regex splitting."""
        # Normalize delimiters
        cleaned = raw.replace("\x02", "").replace("\x03", "").replace("\n", "\r")
        self._frame_buffer += cleaned
        
        if "\r" not in self._frame_buffer: 
            return []
        
        parts = self._frame_buffer.split("\r")
        self._frame_buffer = parts.pop()
        
        extracted = []
        for p in parts:
            p = p.strip()
            if p:
                # Platinum Regex: Split concatenated PC-Link frames while preserving the $ prefix
                # This handles cases where multiple status updates arrive in one serial read
                extracted.extend(f for f in re.split(r'(?=\$)', p) if f)
                
        return extracted

    async def _dispatch_message(self, message: str) -> None:
        """Route messages based on frame content and validate CRCs."""
        if not message:
            return

        # Always put PC-Link responses ($...) into the queue for command correlation
        if message.startswith("$"):
            # ACKs ($05xx) have no CRC, others must be validated
            if message.startswith("$05") or self.validate_crc(message):
                await self.response_queue.put(message)

        # Handle feedback module specifics if callback is provided
        if self._feedback_callback and message.startswith("$1004"):
            if self.validate_crc(message):
                await self._feedback_callback(self._module_group, message)

        # Trigger general event callback for all bus activity
        if asyncio.iscoroutinefunction(self._event_callback):
            await self._event_callback(message)
        else:
            self._event_callback(message)

    def validate_crc(self, message: str) -> bool:
        """Validate the Nikobus CRC-8 for PC-Link frames."""
        # Handle recursion for concatenated frames that escaped extraction
        if message.count("$") > 1:
            return self.validate_crc(message[message.find("$", 1):])

        # Standard ACKs are always valid
        if len(message) == 5 and message.startswith("$05"):
            return True

        try:
            total_len_hex = message[1:3]
            expected_total = int(total_len_hex, 16)
            
            # Nikobus length field is total chars after '$' + 1
            if len(message) != expected_total - 1:
                return False

            payload_with_crc16 = message[:-2]
            expected_crc8 = message[-2:]
            calculated_crc8 = int_to_hex(calc_crc2(payload_with_crc16), 2)
            
            return calculated_crc8.upper() == expected_crc8.upper()
        except Exception:
            return False
