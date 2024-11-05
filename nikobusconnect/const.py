# nikobusconnect/const.py

BAUD_RATE = 9600
COMMANDS_HANDSHAKE = [
    "++++",
    "ATH0",
    "ATZ",
    "$10110000B8CF9D",
    "#L0",
    "#E0",
    "#L0",
    "#E1"
]
EXPECTED_HANDSHAKE_RESPONSE = "$0511"
HANDSHAKE_TIMEOUT = 60
