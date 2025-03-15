#!/usr/bin/env python3

import logging

from ..slash_commands import get_slash_command

__all__ = [
    "user_prompt",
]


async def user_prompt(user_text: str, chat_id: str | None = None) -> str:
    """Store the user's verbatim prompt text for later use and check for slash commands.

    This function checks if the user's prompt contains a slash command and returns
    the content of the matching command file if found.

    Args:
        user_text: The user's original prompt verbatim
        chat_id: The unique ID of the current chat session

    Returns:
        The content of a matched slash command, or a confirmation message if no command is found
    """
    try:
        logging.info(f"Received user prompt for chat ID {chat_id}: {user_text}")

        # Check for slash commands
        command_content = get_slash_command(user_text)
        if command_content:
            logging.info(f"Found slash command in user prompt for chat ID {chat_id}")
            return command_content

        # No slash command found, return the default confirmation
        return "User prompt received"
    except Exception as e:
        logging.warning(f"Exception suppressed in user_prompt: {e!s}", exc_info=True)
        return f"Error processing user prompt: {e!s}"
