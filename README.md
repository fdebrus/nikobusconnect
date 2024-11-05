## Protocol Functions

The `nikobusconnect.protocol` module provides low-level functions for constructing and parsing Nikobus protocol commands.

### Example Usage

```python
from nikobusconnect.protocol import make_pc_link_command

# Construct a PC link command
func = 0xAA  # Example function code
addr = '0012'  # Example address
args = bytes([0x01, 0x02, 0x03])  # Example arguments
command = make_pc_link_command(func, addr, args)
print(f"Command: {command}")
