import logging
from .protocol import make_pc_link_command, calculate_group_number
from .const import COMMAND_EXECUTION_CONFIG

_LOGGER = logging.getLogger(__name__)

class NikobusCommandHandler:
    """Handles sending commands to the Nikobus system with retries and response handling."""

    def __init__(self, nikobus_connection):
        self.nikobus_connection = nikobus_connection

    async def get_output_state(self, address: str, group: int) -> str | None:
        """Get the output state of a module."""
        _LOGGER.debug(f'Getting output state - Address: {address}, Group: {group}') 
        command_code = 0x12 if group == 1 else 0x17
        command = make_pc_link_command(command_code, address)
        try:
            state = await self.send_command_get_answer(command, address)
            _LOGGER.debug(f'Received state for address {address} and group {group}: {state}')
            return state
        except Exception as e:
            _LOGGER.error(f"Error retrieving output state for address {address}, group {group}: {e}")
            return None

    async def set_output_state(self, address: str, channel: int, value: int):
        """Set the output state of a module."""
        group = calculate_group_number(channel)
        command_code = 0x15 if group == 1 else 0x16
        values = self._prepare_command_values(channel, value)
        command = make_pc_link_command(command_code, address, values)
        await self._send_command(command)
        
    async def send_command_get_answer(self, command: str, address: str) -> str | None:
        """Send a command and wait for an acknowledgment and answer."""
        ack_signal, answer_signal = self._prepare_signals(command, address)
        return await self._wait_for_signals(command, ack_signal, answer_signal)
        
    async def _send_command(self, command: str):
        """Send a command to the Nikobus system."""
        try:
            await self.nikobus_connection.send(command)
            _LOGGER.debug("Command sent successfully")
        except Exception as e:
            _LOGGER.error(f"Error sending command: {e}")

    def _prepare_command_values(self, channel: int, value: int) -> bytes:
        """Prepare values for the command based on channel and desired state."""
        values = bytearray(7)
        values[(channel - 1) % 6] = value
        values[6] = 0xFF  # Default termination byte
        return values

    def _prepare_signals(self, command: str, address: str) -> tuple:
        """Prepare acknowledgment and answer signals for a command."""
        command_part = command[3:5]
        ack_signal = f'$05{command_part}'.encode()
        answer_prefix = '$18' if command_part == '11' else '$1C'
        answer_signal = f'{answer_prefix}{address[2:]}{address[:2]}'.encode()
        return ack_signal, answer_signal

    async def _wait_for_signals(self, command: str, ack_signal: bytes, answer_signal: bytes) -> str | None:
        """Wait for acknowledgment and answer signals with retry logic."""
        ack_received = False
        answer_received = None
        for attempt in range(COMMAND_EXECUTION_CONFIG.max_attempts):
            await self._send_command(command)
            _LOGGER.debug(f'Attempt {attempt + 1} of {COMMAND_EXECUTION_CONFIG.max_attempts} for command: {command}')
            ack_deadline = asyncio.get_event_loop().time() + COMMAND_EXECUTION_CONFIG.ack_wait_timeout
            while asyncio.get_event_loop().time() < ack_deadline:
                try:
                    message = await asyncio.wait_for(self.nikobus_connection.read(), timeout=COMMAND_EXECUTION_CONFIG.answer_wait_timeout)
                    _LOGGER.debug(f"Message received: {message}")
                    if ack_signal in message:
                        _LOGGER.debug("Acknowledgment received")
                        ack_received = True
                    if answer_signal in message:
                        _LOGGER.debug("Answer received")
                        answer_received = message
                        break
                    if ack_received and answer_received:
                        return answer_received.decode()
                except asyncio.TimeoutError:
                    _LOGGER.debug("Timeout waiting for acknowledgment or answer signal")
            _LOGGER.debug(f"Retrying for attempt {attempt + 1} due to missing signals.")
        if not ack_received:
            _LOGGER.error(f"Failed to receive acknowledgment for command: {command}")
        if not answer_received:
            _LOGGER.error(f"Failed to receive answer for command: {command}")
        return answer_received.decode() if answer_received else None

