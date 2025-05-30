"""Connection manager for the nikobusconnect library."""

import asyncio
import contextlib
import ipaddress
import logging
import os
import re
from enum import Enum, auto
from typing import Tuple

import serial_asyncio

from nikobusconnect.const import BAUD_RATE, COMMANDS_HANDSHAKE
from nikobusconnect.exceptions import (
    NikobusConnectionError,
    NikobusReadError,
    NikobusSendError,
)

_LOGGER = logging.getLogger(__name__)


# --------------------------------------------------------------------------- #
# Helpers
# --------------------------------------------------------------------------- #
class _ConnType(Enum):
    IP = auto()
    SERIAL = auto()
    UNKNOWN = auto()


def _parse_conn_str(conn: str) -> Tuple[_ConnType, Tuple[str, int] | str | None]:
    """Return (ConnType, parsed target)."""
    _LOGGER.debug("Parsing connection string: %s", conn)
    if ":" in conn:
        host, port_str = conn.split(":", 1)
        with contextlib.suppress(ValueError):
            ipaddress.ip_address(host)
            _LOGGER.debug("Parsed as IP connection: %s:%s", host, port_str)
            return _ConnType.IP, (host, int(port_str))

    if re.fullmatch(r"^(/dev/tty(USB|S)\d+|/dev/serial/by-id/.+)$", conn):
        _LOGGER.debug("Parsed as serial connection: %s", conn)
        return _ConnType.SERIAL, conn

    _LOGGER.debug("Unknown connection string format: %s", conn)
    return _ConnType.UNKNOWN, None


# --------------------------------------------------------------------------- #
# Main class
# --------------------------------------------------------------------------- #
class NikobusConnect:
    """Manages an async transport (IP or serial) to the Nikobus PC-Link."""

    def __init__(self, conn_str: str) -> None:
        _LOGGER.debug("Initializing NikobusConnect with: %s", conn_str)
        self._conn_str = conn_str
        self._type, self._target = _parse_conn_str(conn_str)
        self._reader: asyncio.StreamReader | None = None
        self._writer: asyncio.StreamWriter | None = None

    # ---------------- Context manager ---------------- #
    async def __aenter__(self) -> "NikobusConnect":
        _LOGGER.debug("Entering async context for NikobusConnect")
        await self.connect()
        return self

    async def __aexit__(self, *_exc) -> None:
        _LOGGER.debug("Exiting async context for NikobusConnect")
        await self.disconnect()

    # ---------------- Public API -------------------- #
    async def connect(self) -> None:
        """Open a stream connection to the Nikobus PC-Link and perform handshake."""
        _LOGGER.debug("Connecting to Nikobus interface")
        if self._type is _ConnType.UNKNOWN:
            self._err(f"Invalid connection string: {self._conn_str}", NikobusConnectionError)

        try:
            if self._type is _ConnType.IP and isinstance(self._target, tuple):
                host, port = self._target
                _LOGGER.debug("Opening IP connection to %s:%d", host, port)
                self._reader, self._writer = await asyncio.open_connection(host, port)
                _LOGGER.info("Connected to bridge %s:%d", host, port)

            elif self._type is _ConnType.SERIAL and isinstance(self._target, str):
                if not os.access(self._target, os.R_OK | os.W_OK):
                    self._err(
                        f"No read/write access to serial port: {self._target}",
                        NikobusConnectionError
                    )

                # USB version check before opening the serial connection
                usb_version = self._detect_usb_version(self._target)
                if usb_version == "usb3":
                    self._err(
                        f"Device {self._target} is connected to USB 3.0, which may cause communication issues. "
                        f"Please connect it to a USB 2.0 port.",
                        NikobusConnectionError
                    )

                _LOGGER.debug("Opening serial connection to %s (USB version: %s)", self._target, usb_version)
                self._reader, self._writer = await serial_asyncio.open_serial_connection(
                    url=self._target, baudrate=BAUD_RATE
                )
                _LOGGER.info("Connected to serial port %s", self._target)

        except Exception as err:
            self._err(f"Failed to open transport {self._conn_str}: {err}", NikobusConnectionError)

        _LOGGER.debug("Performing handshake with Nikobus")
        if not await self._handshake():
            await self.disconnect()
            self._err("Handshake failed", NikobusConnectionError)

    async def ping(self) -> None:
        """Test connection open/close via async context."""
        _LOGGER.debug("Pinging Nikobus interface")
        async with self:
            pass

    async def read(self, timeout: float = 5.0) -> bytes:
        """Read one CR-terminated frame; timeout → NikobusReadError (DEBUG log)."""
        _LOGGER.debug("Attempting to read from Nikobus with timeout %.1fs", timeout)
        if not self._reader:
            self._err("Attempted read with no open connection", NikobusReadError)

        try:
            data = await asyncio.wait_for(self._reader.readuntil(b"\r"), timeout)
            _LOGGER.debug("Read successful: %s", data)
            return data
        except TimeoutError:
            _LOGGER.debug("Nikobus read timeout (%.1fs – idle bus)", timeout)
            raise NikobusReadError("Read timed out (idle bus)") from None
        except Exception as err:
            self._err(f"Read failed: {err}", NikobusReadError)

    async def send(self, command: str) -> None:
        """Write a CR-terminated command string to the PC-Link."""
        _LOGGER.debug("Sending command to Nikobus: %s", command)
        if not self._writer:
            self._err("Attempted send with no open connection", NikobusSendError)
        try:
            self._writer.write(command.encode() + b"\r")
            await self._writer.drain()
            _LOGGER.debug("Command sent successfully")
        except Exception as err:
            self._err(f"Send '{command}' failed: {err}", NikobusSendError)

    async def disconnect(self) -> None:
        """Close the transport (if open)."""
        _LOGGER.debug("Disconnecting Nikobus interface")
        if self._writer:
            self._writer.close()
            await self._writer.wait_closed()
            _LOGGER.info("Nikobus connection closed")
        self._reader = self._writer = None

    # ---------------- Internal helpers ---------------- #
    async def _handshake(self) -> bool:
        """Issue required $0DFF / $0EFF handshake commands on cold start."""
        _LOGGER.debug("Running handshake sequence")
        for cmd in COMMANDS_HANDSHAKE:
            try:
                _LOGGER.debug("Sending handshake command: %s", cmd)
                await self.send(cmd)
            except NikobusSendError:
                _LOGGER.debug("Handshake failed on command: %s", cmd)
                return False
        _LOGGER.debug("Handshake completed successfully")
        return True

    @staticmethod
    def _err(msg: str, exc: type[Exception]) -> None:
        """Log and raise exception."""
        _LOGGER.error(msg)
        raise exc(msg)

    @staticmethod
    def _detect_usb_version(devname: str) -> str:
        """
        Returns "usb2" or "usb3" depending on which USB hub the device is connected to.
        Returns "unknown" if not determinable.
        """
        try:
            base = os.path.realpath(f"/sys/class/tty/{os.path.basename(devname)}/device")
            while base and os.path.exists(base):
                # Look for "usbX" in the device name in sysfs path
                if os.path.basename(base).startswith("usb"):
                    if os.path.basename(base).startswith("usb3"):
                        return "usb3"
                    elif os.path.basename(base).startswith("usb2") or os.path.basename(base).startswith("usb1"):
                        return "usb2"
                base = os.path.dirname(base)
        except Exception as e:
            _LOGGER.warning("Could not determine USB version for %s: %s", devname, e)
        return "unknown"
