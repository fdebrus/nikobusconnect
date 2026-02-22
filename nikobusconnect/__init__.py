"""
NikobusConnect: asynchronous library for Nikobus.
"""

from .api import NikobusAPI
from .command import NikobusCommandHandler
from .connection import NikobusConnect
from .listener import NikobusEventListener
from .protocol import (
    calc_crc1,
    calc_crc2,
    calculate_group_number,
    int_to_hex,
    make_pc_link_command,
)

__all__ = [
    "NikobusAPI",
    "NikobusCommandHandler",
    "NikobusConnect",
    "NikobusEventListener",
    "calc_crc1",
    "calc_crc2",
    "calculate_group_number",
    "int_to_hex",
    "make_pc_link_command",
]

__version__ = "1.0.0"  # Jump to 1.0.0 for the Platinum Release
