# nikobusconnect/protocol.py

def int_to_hex(value: int, digits: int) -> str:
    """
    Convert an integer to a hexadecimal string with specified number of digits.

    Args:
        value (int): The integer value to convert.
        digits (int): The number of hexadecimal digits to output.

    Returns:
        str: The hexadecimal string representation of the value.
    """
    return ('{:0' + str(digits) + 'X}').format(value)


def calc_crc1(data: str) -> int:
    """
    Calculate CRC-16/ANSI X3.28 (CRC-16-IBM) for the given data.

    Args:
        data (str): The hexadecimal string data to calculate the CRC on.

    Returns:
        int: The calculated CRC-16 value.
    """
    crc = 0xFFFF
    for j in range(len(data) // 2):
        crc ^= int(data[j * 2: (j + 1) * 2], 16) << 8
        for _ in range(8):
            if (crc & 0x8000):
                crc = (crc << 1) ^ 0x1021
            else:
                crc <<= 1
            crc &= 0xFFFF  # Keep crc within 16 bits
    return crc


def calc_crc2(data: str) -> int:
    """
    Calculate CRC-8 (CRC-8-ATM) for the given data.

    Args:
        data (str): The string data to calculate the CRC on.

    Returns:
        int: The calculated CRC-8 value.
    """
    crc = 0
    for char in data:
        crc ^= ord(char)
        for _ in range(8):
            if crc & 0x80:
                crc = (crc << 1) ^ 0x99
            else:
                crc <<= 1
            crc &= 0xFF  # Keep crc within 8 bits
    return crc


def append_crc1(data: str) -> str:
    """
    Append CRC-16/ANSI X3.28 (CRC-16-IBM) to the given data.

    Args:
        data (str): The hexadecimal string data.

    Returns:
        str: The data string with CRC-16 appended.
    """
    crc = calc_crc1(data)
    return data + int_to_hex(crc, 4)


def append_crc2(data: str) -> str:
    """
    Append CRC-8 (CRC-8-ATM) to the given data.

    Args:
        data (str): The string data.

    Returns:
        str: The data string with CRC-8 appended.
    """
    crc = calc_crc2(data)
    return data + int_to_hex(crc, 2)


def make_pc_link_command(func: int, addr: str, args: bytes = None) -> str:
    """
    Construct a PC link command with the specified function, address, and optional arguments.

    Args:
        func (int): The function code.
        addr (str): The address in hexadecimal string format.
        args (bytes, optional): Additional arguments in bytes. Defaults to None.

    Returns:
        str: The complete PC link command with CRCs.
    """
    addr_int = int(addr, 16)
    data = (
        int_to_hex(func, 2) +
        int_to_hex((addr_int >> 0) & 0xFF, 2) +
        int_to_hex((addr_int >> 8) & 0xFF, 2)
    )
    if args is not None:
        args_hex = args.hex().upper()
        data += args_hex
    # Construct the full command with CRCs
    data_with_crc1 = append_crc1(data)
    command_length = int_to_hex((len(data_with_crc1) // 2) + 1, 2)
    full_command = '$' + command_length + data_with_crc1
    full_command_with_crc2 = append_crc2(full_command)
    return full_command_with_crc2


def calculate_group_number(channel: int) -> int:
    """
    Calculate the group number of a channel.

    Args:
        channel (int): The channel number.

    Returns:
        int: The group number.
    """
    return ((channel - 1) // 6) + 1
