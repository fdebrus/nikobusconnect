# nikobusconnect/const.py

from dataclasses import dataclass, field
from typing import List

@dataclass(frozen=True)
class ConnectionConfig:
    baud_rate: int = 9600
    handshake_commands: List[str] = field(default_factory=lambda: [
        "++++",
        "ATH0",
        "ATZ",
        "$10110000B8CF9D",
        "#L0",
        "#E0",
        "#L0",
        "#E1"
    ])
    expected_handshake_response: str = "$0511"
    handshake_timeout: int = 60

@dataclass(frozen=True)
class MessageParserConfig:
    button_command_prefix: str = "#N"
    ignore_answer: str = "$0E"
    feedback_refresh_command: List[str] = field(default_factory=lambda: ["$1012", "$1017"])
    feedback_module_answer: str = "$1C"
    command_processed: List[str] = field(default_factory=lambda: ["$0515", "$0516"])
    controller_address: str = "$18"
    manual_refresh_commands: List[str] = field(default_factory=lambda: ["$0512", "$0517"])

@dataclass(frozen=True)
class CommandExecutionConfig:
    ack_wait_timeout: float = 2.0
    answer_wait_timeout: float = 5.0
    max_attempts: int = 3

# Instances of config classes
CONNECTION_CONFIG = ConnectionConfig()
MESSAGE_PARSER_CONFIG = MessageParserConfig()
COMMAND_EXECUTION_CONFIG = CommandExecutionConfig()
