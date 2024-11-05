import logging
from .constants import (
    BUTTON_COMMAND_PREFIX,
    IGNORE_ANSWER,
    FEEDBACK_REFRESH_COMMAND,
    FEEDBACK_MODULE_ANSWER,
    COMMAND_PROCESSED,
    CONTROLLER_ADDRESS,
    MANUAL_REFRESH_COMMANDS,
)
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
    """
    Parse a Nikobus message and return a dictionary with its components.

    Args:
        message (str): The raw message string from the Nikobus system.

    Returns:
        dict: A dictionary containing the parsed message details.
    """
    parsed_data = {"type": MessageType.UNKNOWN.value, "message": message}
    
    message_type_map = {
        BUTTON_COMMAND_PREFIX: (MessageType.BUTTON_PRESS, {"data": message[2:8]}),
        IGNORE_ANSWER: (MessageType.IGNORE, {}),
        COMMAND_PROCESSED: (MessageType.COMMAND_ACKNOWLEDGED, {}),
        CONTROLLER_ADDRESS: (MessageType.CONTROLLER_ADDRESS, {"address": message[3:7]}),
        FEEDBACK_REFRESH_COMMAND: (MessageType.FEEDBACK_REFRESH, {"message": message}),
        FEEDBACK_MODULE_ANSWER: (MessageType.FEEDBACK_MODULE_ANSWER, {"message": message}),
    }

    # Check if message matches a specific prefix
    for prefix, (msg_type, extra_data) in message_type_map.items():
        if message.startswith(prefix):
            parsed_data["type"] = msg_type.value
            parsed_data.update(extra_data)
            return parsed_data

    # Check for manual refresh commands
    if any(refresh in message for refresh in MANUAL_REFRESH_COMMANDS):
        parsed_data["type"] = MessageType.MANUAL_REFRESH.value

    return parsed_data
