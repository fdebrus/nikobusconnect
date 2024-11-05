# nikobusconnect/protocol.py

def int_to_hex(value: int, digits: int) -> str:
    """Convert an integer to a zero-padded hexadecimal string."""
    return f'{value:0{digits}X}'


def calc_crc1(data: str) -> int:
    """Calculate CRC-16 (CRC-16-IBM) for a hexadecimal string."""
    crc = 0xFFFF
    for j in range(0, len(data), 2):
        crc ^= int(data[j:j+2], 16) << 8
        for _ in range(8):
            crc = (crc << 1) ^ 0x1021 if crc & 0x8000 else crc << 1
            crc &= 0xFFFF
    return crc


def calc_crc2(data: str) -> int:
    """Calculate CRC-8 (CRC-8-ATM) for a string."""
    crc = 0
    for char in data:
        crc ^= ord(char)
        for _ in range(8):
            crc = (crc << 1) ^ 0x99 if crc & 0x80 else crc << 1
            crc &= 0xFF
    return crc


def append_crc1(data: str) -> str:
    """Append CRC-16 (CRC-16-IBM) to a hexadecimal string."""
    return data + int_to_hex(calc_crc1(data), 4)


def append_crc2(data: str) -> str:
    """Append CRC-8 (CRC-8-ATM) to a string."""
    return data + int_to_hex(calc_crc2(data), 2)


def make_pc_link_command(func: int, addr: str, args: bytes = None) -> str:
    """Construct a PC link command with CRCs, given a function, address, and optional arguments."""
    addr_int = int(addr, 16)
    data = f"{int_to_hex(func, 2)}{int_to_hex(addr_int & 0xFF, 2)}{int_to_hex((addr_int >> 8) & 0xFF, 2)}"
    if args:
        data += args.hex().upper()

    data_with_crc1 = append_crc1(data)
    command_length = int_to_hex((len(data_with_crc1) // 2) + 1, 2)
    full_command = f'${command_length}{data_with_crc1}'
    return append_crc2(full_command)


def calculate_group_number(channel: int) -> int:
    """Calculate the group number for a given channel."""
    return ((channel - 1) // 6) + 1
