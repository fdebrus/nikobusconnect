
# NikobusConnect

NikobusConnect is a Python library that provides an asynchronous interface for connecting to Nikobus home automation systems via IP or Serial connections. It allows you to control and monitor devices connected to a Nikobus system.

## Table of Contents

- [Features](#features)
- [Installation](#installation)
- [Requirements](#requirements)
- [Usage](#usage)
  - [Connecting to Nikobus](#connecting-to-nikobus)
  - [Sending Commands](#sending-commands)
  - [Receiving Messages](#receiving-messages)
  - [Protocol Functions](#protocol-functions)
  - [Setting Output State](#setting-output-state)
  - [Message Parsing](#message-parsing)
- [API Reference](#api-reference)
  - [NikobusConnect](#nikobusconnect-class)
  - [NikobusCommandHandler](#nikobuscommandhandler-class)
  - [Protocol Functions](#protocol-functions-1)
  - [Message Parsing](#message-parsing-function)
- [Examples](#examples)
- [Contributing](#contributing)
- [License](#license)

## Features

- **Asynchronous Communication:** Utilizes `asyncio` for non-blocking I/O operations.
- **Supports IP and Serial Connections:** Connect to Nikobus systems over TCP/IP or via serial ports.
- **Protocol Handling:** Construct and parse Nikobus protocol commands.
- **Command Handling:** Send commands, handle acknowledgments, and manage retries.
- **Message Parsing:** Parse messages received from the Nikobus system.
- **Modular Design:** Easy to integrate into applications like Home Assistant or custom Python scripts.

## Installation

Install the library using pip:

```bash
pip install nikobusconnect
```

## Requirements

- Python 3.7 or higher
- `pyserial-asyncio` package (automatically installed with pip)

## Usage

### Connecting to Nikobus

First, import the `NikobusConnect` class and establish a connection to your Nikobus system.

```python
import asyncio
from nikobusconnect import NikobusConnect

async def main():
    connection_string = '192.168.1.100:8000'
    nikobus = NikobusConnect(connection_string)

    if await nikobus.connect():
        print("Connected to Nikobus system")
        await nikobus.close()
    else:
        print("Failed to connect to Nikobus system")

asyncio.run(main())
```

### Sending Commands

Use the `send` method to send commands to the Nikobus system.

Example command:

```python
command = "$1E12A3B400FF110000FFAA3D7BEE"
await nikobus.send(command)
```

### Receiving Messages

Use the `read` method to read data from the Nikobus system. Example received message:

```python
data = await nikobus.read()
message = data.decode('utf-8').strip()
print(f"Received message: {message}")  # e.g., "$0515$1FA9C20A003F"
```

### Setting Output State

The `set_output_state` function allows setting the state for different Nikobus modules.

- **Parameters:**
  - `address`: The module address as defined in Nikobus software, in a format such as "C9A5".
  - `channel`: The channel to control, ranging from 1 to 6 (for shutter modules) and up to 12 for other modules.
  - `value`: The state or intensity level.

- **Supported values for different modules:**
  - **Switch Module:** `0x00` (Off) or `0x01` (On).
  - **Dimmer Module:** Accepts any value between `0x00` (Off) and `0xFF` (Full On).
  - **Shutter Module:** Supports:
    - `0x00` to stop the cover,
    - `0x01` to open, and
    - `0x02` to close.

Example usage:

```python
await command_handler.set_output_state(address='C9A5', channel=1, value=0xFF)  # Full brightness for dimmer
await command_handler.set_output_state(address='C9A6', channel=2, value=0x00)  # Turn off switch
await command_handler.set_output_state(address='C9A7', channel=3, value=0x02)  # Close shutter
```

### Message Parsing

Use the `parse_message` function to parse messages from the Nikobus system.

Example received message:

```python
from nikobusconnect import parse_message

message = '$0515$0EFF6C0E0060'
parsed = parse_message(message)
print(parsed)
```

## API Reference

### NikobusConnect Class

Class for managing the connection to the Nikobus system.

- **`NikobusConnect(connection_string: str)`**

  Initialize the connection handler with the given connection string.

- **`async connect() -> bool`**

  Connect to the Nikobus system.

- **`async send(command: str)`**

  Send a command to the Nikobus system.

- **`async read()`**

  Read data from the Nikobus system.

- **`async close()`**

  Close the connection to the Nikobus system.

### NikobusCommandHandler Class

Class for handling commands to the Nikobus system.

- **`NikobusCommandHandler(nikobus_connection: NikobusConnect)`**

  Initialize the command handler.

- **`async get_output_state(address: str, group: int) -> Optional[str]`**

  Get the output state of a module.

- **`async set_output_state(address: str, channel: int, value: int)`**

  Set the output state of a module.

### Protocol Functions

Functions for constructing and parsing Nikobus protocol commands.

- **`make_pc_link_command(func: int, addr: str, args: bytes = None) -> str`**

  Construct a PC link command.

- **`calculate_group_number(channel: int) -> int`**

  Calculate the group number of a channel.

### Message Parsing Function

- **`parse_message(message: str) -> dict`**

  Parse a Nikobus message and return its components.

## Examples

### Full Example

```python
import asyncio
from nikobusconnect import NikobusConnect, NikobusCommandHandler, parse_message

async def main():
    connection_string = '/dev/ttyUSB0'
    nikobus = NikobusConnect(connection_string)

    if await nikobus.connect():
        print("Connected to Nikobus system")

        command_handler = NikobusCommandHandler(nikobus)

        await command_handler.set_output_state(address='C9A5', channel=1, value=0xFF)

        state = await command_handler.get_output_state(address='C9A5', group=1)
        print(f"Module state: {state}")

        data = await nikobus.read()
        message = data.decode('utf-8').strip()
        parsed_message = parse_message(message)
        print(f"Parsed message: {parsed_message}")

        await nikobus.close()
    else:
        print("Failed to connect to Nikobus system")

asyncio.run(main())
```

## Contributing

Contributions are welcome! 

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note:** Replace placeholder values with actual values relevant to your Nikobus system.

For questions or support, please open an issue on the [GitHub repository](https://github.com/fdebrus/nikobusconnect).
