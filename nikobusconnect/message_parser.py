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

def parse_message(message):
    # Use individual elements of lists instead of the lists directly
    feedback_refresh_commands = MESSAGE_PARSER_CONFIG.feedback_refresh_command
    command_processed_responses = MESSAGE_PARSER_CONFIG.command_processed

    # Define a dictionary with single string values (no lists as keys)
    message_type_map = {
        MessageType.BUTTON_PRESS: MESSAGE_PARSER_CONFIG.button_command_prefix,
        MessageType.FEEDBACK_MODULE_ANSWER: MESSAGE_PARSER_CONFIG.feedback_module_answer,
        MessageType.CONTROLLER_ADDRESS: MESSAGE_PARSER_CONFIG.controller_address,
    }

    # Check if message matches any known type
    if message in feedback_refresh_commands:
        return MessageType.FEEDBACK_REFRESH
    elif message in command_processed_responses:
        return MessageType.COMMAND_ACKNOWLEDGED
    elif message in message_type_map.values():
        # Match specific message types directly
        for msg_type, value in message_type_map.items():
            if message == value:
                return msg_type
    else:
        return MessageType.UNKNOWN
