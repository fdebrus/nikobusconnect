"""
Nikobus API.
"""

from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Awaitable

_LOGGER = logging.getLogger(__name__)

# Nikobus state constants
STATE_OFF = 0x00
STATE_ON = 0xFF
STATE_OPEN = 0x01
STATE_CLOSE = 0x02

class NikobusAPI:
    """
    High-level API for Nikobus communication.
    Wraps command queueing into logical device actions (lights, switches, covers).
    """

    def __init__(self, command_handler: Any, module_data: dict[str, Any]) -> None:
        """
        Initialize the API.
        
        Args:
            command_handler: The NikobusCommandHandler instance.
            module_data: Dictionary containing module configuration (channels, etc.).
        """
        self._command_handler = command_handler
        self._module_data = module_data

    def _get_channel_info(self, module_key: str, address: str, channel: int) -> dict:
        """Safely retrieve channel metadata from the configuration."""
        module_list = self._module_data.get(module_key, {})
        try:
            # Assumes configuration is keyed by module address
            chan = module_list.get(address, {}).get("channels", [])[channel - 1]
            return chan if chan else {}
        except (IndexError, KeyError, TypeError):
            return {}

    async def _send_bus_command(self, bus_addr: str, completion_handler: Callable | None = None) -> None:
        """Helper to send a standard Nikobus bus trigger (#N...#E1)."""
        await self._command_handler.queue_command(
            f"#N{bus_addr}\r#E1", completion_handler=completion_handler
        )

    async def _dispatch_action(
        self, 
        module_key: str, 
        address: str, 
        channel: int, 
        target_state: int, 
        cmd_key: str, 
        completion_handler: Callable | None = None
    ) -> None:
        """Unified dispatcher for standard module actions (switches and covers)."""
        chan_info = self._get_channel_info(module_key, address, channel)
        bus_cmd = chan_info.get(cmd_key)

        if bus_cmd:
            _LOGGER.debug("Sending bus trigger for %s: %s", address, bus_cmd)
            await self._send_bus_command(bus_cmd, completion_handler)
        else:
            _LOGGER.debug("Setting direct state for %s chan %d to %s", address, channel, hex(target_state))
            await self._command_handler.set_output_state(
                address, channel, target_state, completion_handler=completion_handler
            )

    #### SWITCHES
    async def turn_on_switch(self, address: str, channel: int, completion_handler: Callable | None = None) -> None:
        """Turn on a switch module output."""
        await self._dispatch_action("switch_module", address, channel, STATE_ON, "led_on", completion_handler)

    async def turn_off_switch(self, address: str, channel: int, completion_handler: Callable | None = None) -> None:
        """Turn off a switch module output."""
        await self._dispatch_action("switch_module", address, channel, STATE_OFF, "led_off", completion_handler)

    #### DIMMERS
    async def turn_on_light(
        self, 
        address: str, 
        channel: int, 
        brightness: int, 
        current_brightness: int = 0,
        completion_handler: Callable | None = None
    ) -> None:
        """
        Turn on a dimmer output to a specific brightness.
        
        Args:
            address: Module address.
            channel: Channel number (1-12).
            brightness: Target brightness (0-255).
            current_brightness: Known current state (used to decide if wall LED trigger is needed).
        """
        chan_info = self._get_channel_info("dimmer_module", address, channel)
        
        # Only send simulated button press if the light is currently OFF.
        # This wakes the wall LED without triggering memory recall conflicts on adjustments.
        if current_brightness == 0 and (led_on := chan_info.get("led_on")):
            await self._send_bus_command(led_on)
            # Hardware delay to ensure bus trigger is processed before direct command
            await asyncio.sleep(0.3)

        await self._command_handler.set_output_state(
            address, channel, brightness, completion_handler=completion_handler
        )

    async def turn_off_light(self, address: str, channel: int, completion_handler: Callable | None = None) -> None:
        """Turn off a dimmer output."""
        chan_info = self._get_channel_info("dimmer_module", address, channel)
        
        if led_off := chan_info.get("led_off"):
            await self._send_bus_command(led_off)

        await self._command_handler.set_output_state(
            address, channel, STATE_OFF, completion_handler=completion_handler
        )

    #### COVERS
    async def open_cover(self, address: str, channel: int, completion_handler: Callable | None = None) -> None:
        """Open a cover/roller shutter."""
        await self._dispatch_action("roller_module", address, channel, STATE_OPEN, "led_on", completion_handler)

    async def close_cover(self, address: str, channel: int, completion_handler: Callable | None = None) -> None:
        """Close a cover/roller shutter."""
        await self._dispatch_action("roller_module", address, channel, STATE_CLOSE, "led_off", completion_handler)

    async def stop_cover(self, address: str, channel: int, direction: str, completion_handler: Callable | None = None) -> None:
        """Stop cover movement."""
        chan_info = self._get_channel_info("roller_module", address, channel)
        
        # Determine stop trigger based on movement direction
        cmd_key = "led_on" if direction == "opening" else "led_off"
        bus_cmd = chan_info.get(cmd_key)
        
        if bus_cmd:
            await self._send_bus_command(bus_cmd, completion_handler)
        else:
            await self._command_handler.set_output_state(address, channel, STATE_OFF, completion_handler)

    async def set_output_states_for_module(self, address: str, completion_handler: Callable | None = None) -> None:
        """Batch update all output states for a specific module."""
        await self._command_handler.set_output_states(address, completion_handler=completion_handler)
