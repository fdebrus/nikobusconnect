"""API for the Nikobus protocol library."""

import logging
from typing import Any, Awaitable, Callable, Optional

_LOGGER = logging.getLogger(__name__)

_Completion = Optional[Callable[[], Awaitable[None]]]


class NikobusAPI:
    """
    High-level API for interacting with Nikobus devices.

    This class wraps low-level command handlers and provides
    device-type-specific operations for switches, dimmers, and covers.

    Args:
        coordinator: Object managing Nikobus communication and state.
    """

    def __init__(self, coordinator) -> None:
        _LOGGER.debug("Initializing NikobusAPI")
        self._coordinator = coordinator

    def _ch_info(self, mkey: str, addr: str, ch: int) -> dict[str, Any] | None:
        """Fetch channel info for a given module."""
        try:
            return self._coordinator.dict_module_data[mkey][addr]["channels"][ch - 1]
        except (KeyError, IndexError, TypeError):
            return None

    async def _exec(
        self,
        addr: str,
        ch: int,
        led_cmd: str | None,
        value: int,
        completion_handler: _Completion,
    ) -> None:
        """
        Internal helper to execute a command with optional LED control.
        """
        if led_cmd:
            await self._coordinator.nikobus_command.queue_command(f"#N{led_cmd}\r#E1")
            if completion_handler:
                await completion_handler()
        else:
            await self._coordinator.nikobus_command.set_output_state(
                addr, ch, value, completion_handler=completion_handler
            )
        self._coordinator.set_bytearray_state(addr, ch, value)

    # ----------------------------- Switches -----------------------------
    async def turn_on_switch(
        self, address: str, channel: int, completion_handler: _Completion = None
    ) -> None:
        """Turn ON a switch output."""
        info = self._ch_info("switch_module", address, channel)
        await self._exec(
            address,
            channel,
            info.get("led_on") if info else None,
            0xFF,
            completion_handler,
        )

    async def turn_off_switch(
        self, address: str, channel: int, completion_handler: _Completion = None
    ) -> None:
        """Turn OFF a switch output."""
        info = self._ch_info("switch_module", address, channel)
        await self._exec(
            address,
            channel,
            info.get("led_off") if info else None,
            0x00,
            completion_handler,
        )

    # ----------------------------- Dimmers ------------------------------
    async def turn_on_light(
        self,
        address: str,
        channel: int,
        brightness: int,
        completion_handler: _Completion = None,
    ) -> None:
        """Turn ON a dimmer light with specified brightness."""
        cur = self._coordinator.get_light_brightness(address, channel)
        info = self._ch_info("dimmer_module", address, channel)
        if cur == 0 and info and info.get("led_on"):
            await self._coordinator.nikobus_command.queue_command(
                f"#N{info['led_on']}\r#E1"
            )
        await self._coordinator.nikobus_command.set_output_state(
            address, channel, brightness, completion_handler=completion_handler
        )
        self._coordinator.set_bytearray_state(address, channel, brightness)

    async def turn_off_light(
        self, address: str, channel: int, completion_handler: _Completion = None
    ) -> None:
        """Turn OFF a dimmer light."""
        cur = self._coordinator.get_light_brightness(address, channel)
        info = self._ch_info("dimmer_module", address, channel)
        if cur and info and info.get("led_off"):
            await self._coordinator.nikobus_command.queue_command(
                f"#N{info['led_off']}\r#E1"
            )
        await self._coordinator.nikobus_command.set_output_state(
            address, channel, 0x00, completion_handler=completion_handler
        )
        self._coordinator.set_bytearray_state(address, channel, 0x00)

    # ----------------------------- Covers / Rollers ------------------------------
    async def open_cover(
        self, address: str, channel: int, completion_handler: _Completion = None
    ) -> None:
        """Open a cover (roller shutter)."""
        info = self._ch_info("roller_module", address, channel)
        await self._exec(
            address,
            channel,
            info.get("led_on") if info else None,
            0x01,
            completion_handler,
        )

    async def close_cover(
        self, address: str, channel: int, completion_handler: _Completion = None
    ) -> None:
        """Close a cover (roller shutter)."""
        info = self._ch_info("roller_module", address, channel)
        await self._exec(
            address,
            channel,
            info.get("led_off") if info else None,
            0x02,
            completion_handler,
        )

    async def stop_cover(
        self,
        address: str,
        channel: int,
        direction: str,
        completion_handler: _Completion = None,
    ) -> None:
        """Stop a cover, specifying direction if needed."""
        info = self._ch_info("roller_module", address, channel)
        led = (
            info.get("led_on")
            if direction == "opening"
            else info.get("led_off")
            if info
            else None
        )
        await self._exec(address, channel, led, 0x00, completion_handler)

    # ----------------------------- Bulk Update ------------------------------
    async def set_output_states_for_module(
        self, address: str, completion_handler: _Completion = None
    ) -> None:
        """Set all output states for a module (bulk update)."""
        await self._coordinator.nikobus_command.set_output_states(
            address, completion_handler
        )
