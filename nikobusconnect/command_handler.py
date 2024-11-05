import asyncio
import logging
from .protocol import make_pc_link_command, calculate_group_number
from .constants import (
    COMMAND_EXECUTION_DELAY,
    COMMAND_ACK_WAIT_TIMEOUT,
    COMMAND_ANSWER_WAIT_TIMEOUT,
    MAX_ATTEMPTS,
)

_LOGGER = logging.getLogger(__name__)

class NikobusCommandHandler:
    """Handles sending commands to the Nikobus system with retries and response handling."""

    def __init__(self, nikobus_connection):
        self.nikobus_connection = nikobus_connection
        self._command_queue = asyncio.Queue()
        self._command_task = None
        self._running = False

    async def start(self):
        """Start command processing loop."""
        if not self._running:
            self._running = True
            self._command_task = asyncio.create_task(self._process_commands())

    async def stop(self):
        """Stop command processing loop."""
        self._running = False
        if self._command_task:
            self._command_task.cancel()
            try:
                await self._command_task
            except asyncio.CancelledError:
                _LOGGER.info("Command processing task was cancelled")
            self._command_task = None

    async def get_output_state(self, address: str, group: int) -> str:
        """Get the output state of a module."""
        command_code = 0x12 if group == 1 else 0x17
        command = make_pc_link_command(command_code, address)
        return await self._send_and_wait_for_response(command, address)

    async def set_output_state(self, address: str, channel: int, value: int):
        """Set the output state of a module."""
        group = calculate_group_number(channel)
        command_code = 0x15 if group == 1 else 0x16
        values = self._prepare_command_values(channel, value)
        command = make_pc_link_command(command_code, address, values)
        await self._queue_command(command)

    async def _queue_command(self, command: str):
        """Add a command to the processing queue."""
        await self._command_queue.put(command)

    async def _process_commands(self):
        """Process commands from the queue with a delay."""
        while self._running:
            command = await self._command_queue.get()
            await self._execute_command(command)
            await asyncio.sleep(COMMAND_EXECUTION_DELAY)

    async def _send_command(self, command: str):
        """Send a command to the Nikobus system."""
        try:
            await self.nikobus_connection.send(command)
            _LOGGER.debug("Command sent successfully")
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")

    async def _send_and_wait_for_response(self, command: str, address: str) -> str | None:
        """Send a command and wait for an acknowledgment and answer."""
        ack_signal, answer_signal = self._prepare_signals(command, address)
        return await self._wait_for_signals(command, ack_signal, answer_signal)

    async def _execute_command(self, command: str):
        """Execute a command from the queue."""
        try:
            await self._send_command(command)
            _LOGGER.debug(f"Command executed: {command}")
        except Exception as e:
            _LOGGER.error(f"Failed to execute command: {e}")

    def _prepare_command_values(self, channel: int, value: int) -> bytes:
        """Prepare values for the command based on channel and desired state."""
        values = bytearray(7)
        values[(channel - 1) % 6] = value
        values[6] = 0xFF  # Default termination byte
        return values

    def _prepare_signals(self, command: str, address: str) -> tuple:
        """Prepare acknowledgment and answer signals for a command."""
        command_part = command[3:5]
        ack_signal = f'$05{command_part}'
        answer_prefix = '$18' if command_part == '11' else '$1C'
        answer_signal = f'{answer_prefix}{address[2:]}{address[:2]}'
        return ack_signal, answer_signal

    async def _wait_for_signals(self, command: str, ack_signal: str, answer_signal: str) -> str | None:
        """Wait for acknowledgment and answer signals (placeholder)."""
        # Implement waiting logic based on timeouts here if needed
        return None
