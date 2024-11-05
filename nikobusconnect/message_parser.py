# nikobusconnect/message_parser.py

import logging

_LOGGER = logging.getLogger(__name__)

BUTTON_COMMAND_PREFIX = "#S"  # Example value, replace with actual
IGNORE_ANSWER = "$00"  # Example value, replace with actual
FEEDBACK_REFRESH_COMMAND = "#R"  # Example value, replace with actual
FEEDBACK_MODULE_ANSWER = "$1F"  # Example value, replace with actual
COMMAND_PROCESSED = "#A"  # Example value, replace with actual
CONTROLLER_ADDRESS = "$05"  # Example value, replace with actual
MANUAL_REFRESH_COMMAND = ["$1F", "$0F"]  # Example values, replace with actual

def parse_message(message: str):
    """
    Parse a Nikobus message and return a dictionary with its components.

    Args:
        message (str): The raw message string from the Nikobus system.

    Returns:
        dict: A dictionary containing the parsed message details.
    """
    parsed_data = {}
    if message.startswith(BUTTON_COMMAND_PREFIX):
        parsed_data['type'] = 'button_press'
        parsed_data['data'] = message[2:8]
    elif message.startswith(IGNORE_ANSWER):
        parsed_data['type'] = 'ignore'
    elif message.startswith(COMMAND_PROCESSED):
        parsed_data['type'] = 'command_acknowledged'
    elif message.startswith(CONTROLLER_ADDRESS):
        parsed_data['type'] = 'controller_address'
        parsed_data['address'] = message[3:7]
    elif message.startswith(FEEDBACK_REFRESH_COMMAND):
        parsed_data['type'] = 'feedback_refresh'
        parsed_data['message'] = message
    elif message.startswith(FEEDBACK_MODULE_ANSWER):
        parsed_data['type'] = 'feedback_module_answer'
        parsed_data['message'] = message
    elif any(refresh in message for refresh in MANUAL_REFRESH_COMMAND):
        parsed_data['type'] = 'manual_refresh'
        parsed_data['message'] = message
    else:
        parsed_data['type'] = 'unknown'
        parsed_data['message'] = message

    return parsed_data
