# nikobusconnect/connection.py

import logging
import asyncio
import serial_asyncio
import ipaddress
import re
from serial.serialutil import SerialException

_LOGGER = logging.getLogger(__name__)

class NikobusConnect:
    """Manages connection to a Nikobus system via IP or Serial."""

    def __init__(self, connection_string: str):
        """Initialize the connection handler with the given connection string."""
        self._connection_string = connection_string
        self._connection_type = self._determine_connection_type()
        self._nikobus_reader = None
        self._nikobus_writer = None

    async def connect(self) -> bool:
        """Connect to the Nikobus system using the connection string."""
        connect_func = self._connect_ip if self._connection_type == "IP" else self._connect_serial
        try:
            await connect_func()
            if await self._perform_handshake():
                _LOGGER.info("Nikobus handshake successful")
                return True
            return False
        except (OSError, asyncio.TimeoutError) as err:
            _LOGGER.error(f"Connection error with {self._connection_string}: {err}")
            return False

    async def _connect_ip(self):
        """Establish an IP connection to the Nikobus system."""
        host, port_str = self._connection_string.split(":")
        port = int(port_str)
        try:
            self._nikobus_reader, self._nikobus_writer = await asyncio.open_connection(host, port)
            _LOGGER.info(f"Connected to bridge {host}:{port}")
        except (OSError, ValueError) as err:
            _LOGGER.error(f"Failed to connect to bridge {self._connection_string} - {err}")

    async def _connect_serial(self):
        """Establish a serial connection to the Nikobus system."""
        try:
            self._nikobus_reader, self._nikobus_writer = await serial_asyncio.open_serial_connection(
                url=self._connection_string, baudrate=BAUD_RATE
            )
            _LOGGER.info(f"Connected to serial port {self._connection_string}")
        except (OSError, SerialException) as err:
            _LOGGER.error(f"Failed to connect to serial port {self._connection_string} - {err}")

    def _determine_connection_type(self) -> str:
        """Determine the connection type based on the connection string."""
        if re.match(r'^(/dev/tty(USB|S)\d+|/dev/serial/by-id/.+)$', self._connection_string):
            return "Serial"
        try:
            ipaddress.ip_address(self._connection_string.split(':')[0])
            return "IP"
        except ValueError:
            return "Unknown"

    async def _perform_handshake(self) -> bool:
        """Perform a handshake with the Nikobus system to verify the connection."""
        return all(await self.send(command) for command in COMMANDS_HANDSHAKE)

    async def read(self):
        """Read data from the Nikobus system."""
        if not self._nikobus_reader:
            _LOGGER.error("Reader is not available for reading data.")
            return None
        return await self._nikobus_reader.readuntil(b'\r')

    async def send(self, command: str) -> bool:
        """Send a command to the Nikobus system."""
        if not self._nikobus_writer:
            _LOGGER.error("Writer is not available for sending commands.")
            return False
        try:
            self._nikobus_writer.write(command.encode() + b'\r')
            await self._nikobus_writer.drain()
            return True
        except (asyncio.TimeoutError, OSError) as err:
            _LOGGER.error(f"Error sending command '{command}': {err}")
            return False
        except Exception as e:
            _LOGGER.exception(f"Unhandled exception while sending command '{command}': {e}")
            return False

    async def close(self):
        """Close the connection to the Nikobus system."""
        if self._nikobus_writer:
            self._nikobus_writer.close()
            await self._nikobus_writer.wait_closed()
            _LOGGER.info("Nikobus connection closed")
