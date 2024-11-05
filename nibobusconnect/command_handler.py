# nikobusconnect/command_handler.py

import asyncio
import logging
from .protocol import make_pc_link_command, calculate_group_number

_LOGGER = logging.getLogger(__name__)

COMMAND_EXECUTION_DELAY = 0.5  # seconds
COMMAND_ACK_WAIT_TIMEOUT = 2.0  # seconds
COMMAND_ANSWER_WAIT_TIMEOUT = 5.0  # seconds
MAX_ATTEMPTS = 3  # Max retries for sending commands

class NikobusCommandHandler:
    """
    Handles command processing for Nikobus.

    This class is responsible for sending commands to the Nikobus system,
    handling acknowledgments and responses, and managing command retries.
    """

    def __init__(self, nikobus_connection):
        """
        Initialize the command handler.

        Args:
            nikobus_connection: An instance of NikobusConnect.
        """
        self._running = False
        self.nikobus_connection = nikobus_connection
        self._command_queue = asyncio.Queue()
        self._command_task = None

    async def start(self):
        """Start the command processing loop."""
        if not self._running:
            self._running = True
            self._command_task = asyncio.create_task(self.process_commands())

    async def stop(self):
        """Stop the command processing loop."""
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
        _LOGGER.debug(f'Getting output state - Address: {address}, Group: {group}')
        command_code = 0x12 if int(group) == 1 else 0x17
        command = make_pc_link_command(command_code, address)
        return await self.send_command_get_answer(command, address)

    async def set_output_state(self, address: str, channel: int, value: int) -> None:
        """Set the output state of a module."""
        _LOGGER.debug(f'Setting output state - Address: {address}, Channel: {channel}, Value: {value}')
        group = calculate_group_number(channel)
        # Prepare values for the command
        values = self._prepare_values_for_command(address, group, channel, value)
        command_code = 0x15 if int(group) == 1 else 0x16
        command = make_pc_link_command(command_code, address, values)
        await self.queue_command(command)

    async def queue_command(self, command: str) -> None:
        """Queue a command for processing."""
        _LOGGER.debug(f'Queueing command: {command}')
        await self._command_queue.put(command)

    async def process_commands(self) -> None:
        """Process commands from the queue."""
        _LOGGER.info("Nikobus Command Processing starting")
        while self._running:
            command = await self._command_queue.get()
            _LOGGER.debug(f'Processing command: {command}')
            await self._execute_command(command)
            await asyncio.sleep(COMMAND_EXECUTION_DELAY)

    async def send_command(self, command: str):
        """Send a command to the Nikobus system."""
        _LOGGER.debug(f'Sending command: {command}')
        try:
            await self.nikobus_connection.send(command)
            _LOGGER.debug('Command sent successfully')
        except Exception as e:
            _LOGGER.error(f'Error sending command: {e}')

    async def send_command_get_answer(self, command: str, address: str) -> str | None:
        """Send a command and wait for an answer from the Nikobus system."""
        _LOGGER.debug(f'Sending command {command} to address {address}, waiting for answer')
        ack_signal, answer_signal = self._prepare_ack_and_answer_signals(command, address)
        return await self._wait_for_ack_and_answer(command, ack_signal, answer_signal)

    async def _execute_command(self, command: str):
        """Execute a command and handle potential errors."""
        try:
            await self.send_command(command)
            _LOGGER.debug(f'Command executed: {command}')
        except Exception as e:
            _LOGGER.error(f'Failed to execute command "{command}": {e}')

    def _prepare_values_for_command(self, address: str, group: int, channel: int, value: int) -> bytes:
        """Prepare values for a command based on the desired state."""
        # Implementation depends on how module states are managed.
        # For now, we'll create a placeholder byte array.
        values = bytearray(7)
        # Set the desired channel to the value.
        channel_index = (channel - 1) % 6
        values[channel_index] = value
        # Last byte is usually 0xFF
        values[6] = 0xFF
        return values

    def _prepare_ack_and_answer_signals(self, command: str, address: str) -> tuple:
        """Prepare the acknowledgment and answer signals for a command."""
        command_part = command[3:5]
        ack_signal = f'$05{command_part}'
        answer_prefix = '$18' if command_part == '11' else '$1C'
        answer_signal = f'{answer_prefix}{address[2:]}{address[:2]}'
        return ack_signal, answer_signal

    async def _wait_for_ack_and_answer(self, command: str, ack_signal: str, answ
