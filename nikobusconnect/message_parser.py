import logging
from .const import MESSAGE_PARSER_CONFIG
from enum import Enum

_LOGGER = logging.getLogger(__name__)

class MessageType(Enum):
    BUTTON_PRESS = "button_press"
    IGNORE = "ignore"
    COMMAND_ACKNOWLEDGED = "command_acknowledged"
    CONTROLLER_ADDRESS = "controller_address"
    FEEDBACK_REFRESH = "feedback_refresh"
    FEEDBACK_MODULE_ANSWER = "feedback_module_answer"
    MANUAL_REFRESH = "manual_refresh"
    UNKNOWN = "unknown"

def parse_message(message: str) -> dict:
    """Parse a Nikobus message and return a dictionary with its components."""
    parsed_data = {"type": MessageType.UNKNOWN.value, "message": message}
    
    message_type_map = {
        MESSAGE_PARSER_CONFIG.button_command_prefix: (MessageType.BUTTON_PRESS, {"data": message[2:8]}),
        MESSAGE_PARSER_CONFIG.ignore_answer: (MessageType.IGNORE, {}),
        MESSAGE_PARSER_CONFIG.command_processed: (MessageType.COMMAND_ACKNOWLEDGED, {}),
        MESSAGE_PARSER_CONFIG.controller_address: (MessageType.CONTROLLER_ADDRESS, {"address": message[3:7]}),
        MESSAGE_PARSER_CONFIG.feedback_refresh_command: (MessageType.FEEDBACK_REFRESH, {"message": message}),
        MESSAGE_PARSER_CONFIG.feedback_module_answer: (MessageType.FEEDBACK_MODULE_ANSWER, {"message": message}),
    }

    # Check if message matches a specific prefix
    for prefix, (msg_type, extra_data) in message_type_map.items():
        if message.startswith(prefix):
            parsed_data["type"] = msg_type.value
            parsed_data.update(extra_data)
            return parsed_data

    # Check for manual refresh commands
    if any(refresh in message for refresh in MESSAGE_PARSER_CONFIG.manual_refresh_commands):
        parsed_data["type"] = MessageType.MANUAL_REFRESH.value

    return parsed_data
