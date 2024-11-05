# nikobusconnect/__init__.py

from .connection import NikobusConnect
from .protocol import (
    int_to_hex,
    calc_crc1,
    calc_crc2,
    append_crc1,
    append_crc2,
    make_pc_link_command,
    calculate_group_number,
)

__all__ = [
    'NikobusConnect',
    'int_to_hex',
    'calc_crc1',
    'calc_crc2',
    'append_crc1',
    'append_crc2',
    'make_pc_link_command',
    'calculate_group_number',
]

__version__ = '0.1.0'
