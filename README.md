
# NikobusConnect

NikobusConnect is a Python library that provides an asynchronous interface for connecting to Nikobus home automation systems via IP or Serial connections. It allows you to control and monitor devices connected to a Nikobus system.

## Features

- **Asynchronous Communication:** Utilizes `asyncio` for non-blocking I/O operations.
- **Supports IP and Serial Connections:** Connect to Nikobus systems over TCP/IP or via serial ports.
- **Automatic Handshake:** Performs the full PC-Link modem initialization sequence on connect.
- **Protocol Handling:** Construct and parse Nikobus protocol commands with CRC-16 and CRC-8 validation.
- **Queue-Based Command Processing:** Sequential command execution with deduplication and retry logic.
- **Event Listener:** Background listener with per-address group tracking, connection-lost detection, and feedback module support.
- **High-Level API:** Control switches, dimmers, and covers with optimistic state updates.
- **Button Address Utilities:** Encode and decode Nikobus button addresses (`#Nxxxxxx` format).
- **Modular Design:** Easy to integrate into Home Assistant or custom Python scripts.

## Installation

Install the library using pip:

```bash
pip install nikobusconnect
```

## Requirements

- Python 3.10 or higher
- `pyserial-asyncio` package (automatically installed with pip)

## Usage

### Connecting to Nikobus

The connection handler automatically performs the handshake sequence after connecting.

```python
import asyncio
from nikobusconnect import NikobusConnect

async def main():
    # TCP/IP connection
    nikobus = NikobusConnect('192.168.1.100:8000')
    # Or serial connection
    # nikobus = NikobusConnect('/dev/ttyUSB0')

    await nikobus.connect()
    print("Connected to Nikobus system")

    # Verify the PC-Link is responsive
    await nikobus.ping()

    await nikobus.disconnect()

asyncio.run(main())
```

### Setting Up the Listener and Command Handler

```python
import asyncio
from nikobusconnect import NikobusConnect, NikobusEventListener, NikobusCommandHandler

async def on_event(message: str):
    print(f"Bus event: {message}")

async def on_feedback(group: int, message: str):
    print(f"Feedback group {group}: {message}")

async def main():
    connection = NikobusConnect('192.168.1.100:8000')
    await connection.connect()

    listener = NikobusEventListener(
        connection=connection,
        event_callback=on_event,
        feedback_callback=on_feedback,
        has_feedback_module=True,
    )

    command_handler = NikobusCommandHandler(
        connection=connection,
        listener=listener,
    )

    await listener.start()
    await command_handler.start()

    # Set a channel state
    await command_handler.set_output_state(address='C9A5', channel=1, value=0xFF)

    # Get the current state of a module
    state = await command_handler.get_output_state(address='C9A5', group=1)
    print(f"Module state: {state}")

    await command_handler.stop()
    await listener.stop()
    await connection.disconnect()

asyncio.run(main())
```

### Using the High-Level API

```python
from nikobusconnect import NikobusAPI

# module_data describes your Nikobus module configuration
module_data = {
    "switch_module": {
        "C9A5": {
            "channels": [
                {"led_on": "ABC123", "led_off": "ABC124"},
                # ... more channels
            ]
        }
    }
}

api = NikobusAPI(command_handler, module_data)

# Switches
await api.turn_on_switch('C9A5', channel=1)
await api.turn_off_switch('C9A5', channel=1)

# Dimmers (brightness 0-255)
await api.turn_on_light('C9A6', channel=1, brightness=200)
await api.turn_off_light('C9A6', channel=1)

# Covers
await api.open_cover('C9A7', channel=1)
await api.close_cover('C9A7', channel=1)
await api.stop_cover('C9A7', channel=1, direction='opening')
```

### Setting Output State

The `set_output_state` method sets the state for different Nikobus modules.

- **Parameters:**
  - `address`: The module address (e.g., `"C9A5"`).
  - `channel`: The channel to control (1-12).
  - `value`: The state or intensity level.

- **Supported values:**
  - **Switch Module:** `0x00` (Off) or `0xFF` (On).
  - **Dimmer Module:** `0x00` (Off) to `0xFF` (Full brightness).
  - **Shutter Module:** `0x00` (Stop), `0x01` (Open), `0x02` (Close).

```python
await command_handler.set_output_state(address='C9A5', channel=1, value=0xFF)  # Switch on
await command_handler.set_output_state(address='C9A6', channel=2, value=0x80)  # Dimmer 50%
await command_handler.set_output_state(address='C9A7', channel=3, value=0x02)  # Close shutter
```

### Protocol Utilities

```python
from nikobusconnect import (
    make_pc_link_command,
    calc_crc1,
    calc_crc2,
    calculate_group_number,
    nikobus_to_button_address,
    nikobus_button_to_module,
)

# Build a PC-Link command
command = make_pc_link_command(func=0x15, addr='C9A5', args=bytearray([0xFF, 0, 0, 0, 0, 0, 0xFF]))

# Calculate CRC values
crc16 = calc_crc1("1512A5C9")
crc8 = calc_crc2("$1E1512A5C9")

# Determine group number for a channel
group = calculate_group_number(7)  # Returns 2

# Convert module address to button address
button_addr = nikobus_to_button_address("A1B2C3", button="1A")

# Reverse: button address back to module address
module_addr, button_label = nikobus_button_to_module("#NAABBCC")
```

## API Reference

### NikobusConnect

Manages the asynchronous connection (Serial or TCP) to the Nikobus PC-Link.

| Method | Description |
|--------|-------------|
| `connect()` | Establish the connection and perform handshake |
| `disconnect()` | Close the connection |
| `ping()` | Verify the PC-Link is responsive |
| `send(command)` | Send a command string to the bus |
| `read()` | Read a single CR-terminated frame |
| `is_connected` | Property: connection status |

### NikobusEventListener

Listens to the PC-Link serial stream and dispatches decoded frames.

| Method | Description |
|--------|-------------|
| `start()` | Start the background listening task |
| `stop()` | Stop the listener |
| `set_pending_query_group(addr, group)` | Record which group is being queried |
| `validate_crc(message)` | Validate CRC-8 for a PC-Link frame |

### NikobusCommandHandler

Handles queue-based command processing with retry logic.

| Method | Description |
|--------|-------------|
| `start()` | Start the command processing loop |
| `stop()` | Stop the processing loop |
| `queue_command(command, address, ...)` | Queue a command for processing |
| `get_output_state(address, group)` | Get the output state of a module |
| `set_output_state(address, channel, value)` | Set a single channel state |
| `set_output_states(address)` | Batch update all outputs for a module |
| `set_bytearray_state(address, channel, value)` | Update internal state buffer |
| `resolve_pending_get(address, group, state)` | Resolve a pending GET via feedback fast-path |

### NikobusAPI

High-level API for device control.

| Method | Description |
|--------|-------------|
| `turn_on_switch(address, channel)` | Turn on a switch output |
| `turn_off_switch(address, channel)` | Turn off a switch output |
| `turn_on_light(address, channel, brightness)` | Turn on a dimmer to specific brightness |
| `turn_off_light(address, channel)` | Turn off a dimmer |
| `open_cover(address, channel)` | Open a cover/roller shutter |
| `close_cover(address, channel)` | Close a cover/roller shutter |
| `stop_cover(address, channel, direction)` | Stop cover movement |
| `set_output_states_for_module(address)` | Batch update all outputs |

### Protocol Functions

| Function | Description |
|----------|-------------|
| `make_pc_link_command(func, addr, args)` | Construct a PC-Link command |
| `make_pc_link_inventory_command(payload)` | Construct an inventory command |
| `calc_crc1(data)` | Calculate CRC-16/ANSI X3.28 |
| `calc_crc2(data)` | Calculate CRC-8-ATM |
| `append_crc1(data)` | Append CRC-16 to data |
| `append_crc2(data)` | Append CRC-8 to data |
| `calculate_group_number(channel)` | Get group number for a channel |
| `nikobus_to_button_address(hex_address, button)` | Convert module address to `#Nxxxxxx` |
| `nikobus_button_to_module(button_hex)` | Convert `#Nxxxxxx` back to module address |
| `reverse_24bit_to_hex(n)` | Reverse 24-bit value to hex |
| `int_to_hex(value, digits)` | Integer to hex string with padding |

### Exceptions

All exceptions inherit from `NikobusError`:

| Exception | Description |
|-----------|-------------|
| `NikobusError` | Base exception |
| `NikobusConnectionError` | Connection failures |
| `NikobusSendError` | Command transmission failures |
| `NikobusReadError` | Data read failures |
| `NikobusTimeoutError` | Operation timeouts |
| `NikobusDataError` | Data-related errors |

## Contributing

Contributions are welcome!

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note:** Replace placeholder values with actual values relevant to your Nikobus system.

For questions or support, please open an issue on the [GitHub repository](https://github.com/fdebrus/nikobusconnect).
