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
    """Parse a message and determine its type."""
    _LOGGER.debug(f"Parsing received message: {message}")

    # Check for message types based on prefix or exact match
    if message.startswith(MESSAGE_PARSER_CONFIG.button_command_prefix):
        _LOGGER.debug("Message type identified as BUTTON_PRESS")
        return MessageType.BUTTON_PRESS
    elif any(message.startswith(cmd) for cmd in MESSAGE_PARSER_CONFIG.feedback_refresh_command):
        _LOGGER.debug("Message type identified as FEEDBACK_REFRESH")
        return MessageType.FEEDBACK_REFRESH
    elif any(message.startswith(cmd) for cmd in MESSAGE_PARSER_CONFIG.command_processed):
        _LOGGER.debug("Message type identified as COMMAND_ACKNOWLEDGED")
        return MessageType.COMMAND_ACKNOWLEDGED
    elif message.startswith(MESSAGE_PARSER_CONFIG.controller_address):
        _LOGGER.debug("Message type identified as CONTROLLER_ADDRESS")
        return MessageType.CONTROLLER_ADDRESS
    elif message.startswith(MESSAGE_PARSER_CONFIG.feedback_module_answer):
        _LOGGER.debug("Message type identified as FEEDBACK_MODULE_ANSWER")
        return MessageType.FEEDBACK_MODULE_ANSWER
    elif any(message.startswith(cmd) for cmd in MESSAGE_PARSER_CONFIG.manual_refresh_commands):
        _LOGGER.debug("Message type identified as MANUAL_REFRESH")
        return MessageType.MANUAL_REFRESH
    else:
        _LOGGER.debug("Message type identified as UNKNOWN")
        return MessageType.UNKNOWN
