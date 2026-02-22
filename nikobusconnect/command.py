"""
Nikobus Command Handler.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Optional

from .protocol import make_pc_link_command

_LOGGER = logging.getLogger(__name__)

class NikobusCommandHandler:
    """Handles sequential command execution and response correlation for Nikobus."""

    def __init__(self, connection: Any, response_queue: asyncio.Queue[str]) -> None:
        """
        Initialize the command handler.

        Args:
            connection: The NikobusConnect instance.
            response_queue: The queue where the listener places incoming PC-Link frames.
        """
        self._connection = connection
        self._response_queue = response_queue
        self._command_lock = asyncio.Lock()
        
        # State tracking for module outputs
        self._module_states: dict[str, bytearray] = {}

    def set_cached_state(self, address: str, channel: int, state: int) -> None:
        """Update the internal state buffer for a module's channels."""
        if address not in self._module_states:
            self._module_states[address] = bytearray([0] * 6)
        
        # Nikobus uses 1-based channel indexing; map to 0-based for bytearray
        idx = (channel - 1) % 6
        self._module_states[address][idx] = state

    async def queue_command(
        self, 
        command: str, 
        completion_handler: Optional[Callable] = None
    ) -> None:
        """Queue a raw command string for sequential execution."""
        async with self._command_lock:
            try:
                _LOGGER.debug("Queueing command: %s", command)
                await self._connection.send(command)
                
                if completion_handler:
                    if asyncio.iscoroutinefunction(completion_handler):
                        await completion_handler()
                    else:
                        completion_handler()
                        
                # Small inter-command delay to prevent bus collisions
                await asyncio.sleep(0.1)
            except Exception as err:
                _LOGGER.error("Failed to execute command %s: %s", command, err)
                raise

    async def set_output_state(
        self, 
        address: str, 
        channel: int, 
        state: int, 
        completion_handler: Optional[Callable] = None
    ) -> None:
        """Set a specific channel's output state using PC-Link protocol ($12)."""
        self.set_cached_state(address, channel, state)
        
        # Determine group (1 for channels 1-6, 2 for 7-12)
        group = 0x12 if 1 <= channel <= 6 else 0x15
        data = self._module_states[address]
        
        pc_command = make_pc_link_command(group, address, data)
        await self.queue_command(pc_command, completion_handler)

    async def set_output_states(
        self, 
        address: str, 
        completion_handler: Optional[Callable] = None
    ) -> None:
        """Batch update all 6 outputs in a group for a specific module."""
        if address not in self._module_states:
            _LOGGER.warning("No state cached for module %s, skipping batch update", address)
            return

        # Typically, we refresh Group 1 ($12). Group 2 ($15) requires a separate call.
        pc_command = make_pc_link_command(0x12, address, self._module_states[address])
        await self.queue_command(pc_command, completion_handler)

    async def wait_for_response(self, timeout: float = 2.0) -> str:
        """Wait for a specific response from the Nikobus PC-Link."""
        try:
            return await asyncio.wait_for(self._response_queue.get(), timeout=timeout)
        except asyncio.TimeoutError:
            _LOGGER.warning("Timed out waiting for Nikobus response")
            return ""
