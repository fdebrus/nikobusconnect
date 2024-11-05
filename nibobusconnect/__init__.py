# nikobusconnect/__init__.py

from .connection import NikobusConnect
from .command_handler import NikobusCommandHandler
from .protocol import (
    int_to_hex,
    calc_crc1,
    calc_crc2,
    append_crc1,
    append_crc2,
    make_pc_link_command,
    calculate_group_number,
)
from .message_parser import parse_message

__all__ = [
    'NikobusConnect',
    'NikobusCommandHandler',
    'int_to_hex',
    'calc_crc1',
    'calc_crc2',
    'append_crc1',
    'append_crc2',
    'make_pc_link_command',
    'calculate_group_number',
    'parse_message',
]

__version__ = '0.1.0'
