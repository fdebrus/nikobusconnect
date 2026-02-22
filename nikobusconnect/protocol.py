"""
Nikobus Protocol Helpers.
"""

from __future__ import annotations

import logging

_LOGGER = logging.getLogger(__name__)

def int_to_hex(val: int, length: int) -> str:
    """Convert integer to uppercase hex string with padding."""
    return f"{val:0{length}X}"

def calc_crc1(data: str) -> int:
    """
    Calculate CRC-16/ANSI X3.28 (CRC-16-IBM).
    Optimized for Python using native byte conversion.
    """
    crc = 0xFFFF
    # Python bytes.fromhex is faster than manual slicing of strings
    for byte in bytes.fromhex(data):
        crc ^= (byte << 8)
        for _ in range(8):
            if (crc >> 15) & 1:
                crc = (crc << 1) ^ 0x1021
            else:
                crc = crc << 1
    return crc & 0xFFFF

def calc_crc2(payload: str) -> int:
    """
    Calculate Nikobus CRC-8 (XOR-sum of bytes).
    Used for validating frames received from the PC-Link.
    """
    crc = 0
    for byte in bytes.fromhex(payload):
        crc ^= byte
    return crc & 0xFF

def make_pc_link_command(func: int, addr: str, data: bytearray | None = None) -> str:
    """
    Construct a Nikobus PC-Link command hex string ($...).
    
    Args:
        func: The function code (e.g., 0x12, 0x15).
        addr: The module address (4-digit hex string).
        data: Optional bytearray for output states.
    """
    # Address is stored as Big-Endian string (e.g. 1A2B) 
    # but protocol expects Little-Endian bytes (2B1A)
    addr_int = int(addr, 16)
    addr_le = addr_int.to_bytes(2, byteorder='little').hex().upper()
    
    # Base command part
    cmd_part = f"{int_to_hex(func, 2)}{addr_le}"
    
    if data:
        cmd_part += data.hex().upper()
        
    # Calculate CRC-16 for the command payload
    crc16 = int_to_hex(calc_crc1(cmd_part), 4)
    full_payload = f"{cmd_part}{crc16}"
    
    # Calculate Nikobus CRC-8 for the final frame
    # Length is total chars + 1 for the '$'
    total_len = int_to_hex(len(full_payload) + 3, 2)
    final_payload = f"{total_len}{full_payload}"
    crc8 = int_to_hex(calc_crc2(final_payload), 2)
    
    return f"${final_payload}{crc8}"

def calculate_group_number(channel: int) -> int:
    """Determine the module group (1 for channels 1-6, 2 for 7-12)."""
    return 1 if 1 <= channel <= 6 else 2
