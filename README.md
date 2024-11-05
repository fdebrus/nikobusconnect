
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
  - [Command Handling](#command-handling)
  - [Protocol Functions](#protocol-functions)
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
    # Replace with your Nikobus connection string (e.g., '192.168.1.100:8000' or '/dev/ttyUSB0')
    connection_string = '192.168.1.100:8000'
    nikobus = NikobusConnect(connection_string)

    if await nikobus.connect():
        print("Connected to Nikobus system")
        # Your code here
        await nikobus.close()
    else:
        print("Failed to connect to Nikobus system")

asyncio.run(main())
```

### Sending Commands

Use the `send` method to send commands to the Nikobus system.

```python
await nikobus.send('#SOME_COMMAND')
```

### Receiving Messages

Use the `read` method to read data from the Nikobus system.

```python
data = await nikobus.read()
message = data.decode('utf-8').strip()
print(f"Received message: {message}")
```

### Command Handling

You can use the `NikobusCommandHandler` class to manage command queues and handle responses.

```python
from nikobusconnect import NikobusCommandHandler

# Initialize the command handler with the connection
command_handler = NikobusCommandHandler(nikobus)
await command_handler.start()

# Queue a command
await command_handler.queue_command('#SOME_COMMAND')

# Stop the command handler when done
await command_handler.stop()
```

### Protocol Functions

Use the protocol functions to construct commands and calculate checksums.

```python
from nikobusconnect import make_pc_link_command

# Construct a PC link command
func = 0xE2  # Function code
addr = '0012'  # Module address
args = bytes([0x01])  # Arguments
command = make_pc_link_command(func, addr, args)
print(f"Command: {command}")
```

### Message Parsing

Use the `parse_message` function to parse messages from the Nikobus system.

```python
from nikobusconnect import parse_message

message = '#S123456'
parsed = parse_message(message)
print(parsed)
# Output: {'type': 'button_press', 'data': '123456'}
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

- **`async start()`**

  Start the command processing loop.

- **`async stop()`**

  Stop the command processing loop.

- **`async queue_command(command: str)`**

  Queue a command for processing.

- **`async get_output_state(address: str, group: int) -> Optional[str]`**

  Get the output state of a module.

- **`async set_output_state(address: str, channel: int, value: int)`**

  Set the output state of a module.

### Protocol Functions

Functions for constructing and parsing Nikobus protocol commands.

- **`int_to_hex(value: int, digits: int) -> str`**

  Convert an integer to a hexadecimal string with specified number of digits.

- **`calc_crc1(data: str) -> int`**

  Calculate CRC-16/ANSI X3.28 (CRC-16-IBM) for the given data.

- **`calc_crc2(data: str) -> int`**

  Calculate CRC-8 (CRC-8-ATM) for the given data.

- **`append_crc1(data: str) -> str`**

  Append CRC-16 to the given data.

- **`append_crc2(data: str) -> str`**

  Append CRC-8 to the given data.

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
    connection_string = '192.168.1.100:8000'  # Replace with your connection string
    nikobus = NikobusConnect(connection_string)
    if await nikobus.connect():
        print("Connected to Nikobus system")

        # Initialize the command handler
        command_handler = NikobusCommandHandler(nikobus)
        await command_handler.start()

        # Set the output state of a module
        await command_handler.set_output_state(address='0012', channel=1, value=255)

        # Get the output state of a module
        state = await command_handler.get_output_state(address='0012', group=1)
        print(f"Module state: {state}")

        # Read and parse messages
        data = await nikobus.read()
        message = data.decode('utf-8').strip()
        parsed_message = parse_message(message)
        print(f"Parsed message: {parsed_message}")

        # Stop the command handler
        await command_handler.stop()

        # Close the connection
        await nikobus.close()
    else:
        print("Failed to connect to Nikobus system")

asyncio.run(main())
```

## Contributing

Contributions are welcome! Please follow these steps:

1. Fork the repository on GitHub.
2. Create a new branch: `git checkout -b feature/your-feature-name`.
3. Commit your changes: `git commit -am 'Add your feature'`.
4. Push to the branch: `git push origin feature/your-feature-name`.
5. Submit a pull request.

For major changes, please open an issue first to discuss what you would like to change.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

**Note:** Replace placeholder values like IP addresses, module addresses, and commands with actual values relevant to your Nikobus system.

---

For any questions or support, please open an issue on the [GitHub repository](https://github.com/yourusername/nikobusconnect) or contact the author at `your.email@example.com`.
