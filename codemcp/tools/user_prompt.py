#!/usr/bin/env python3

import logging

__all__ = [
    "user_prompt",
]


async def user_prompt(user_text: str, chat_id: str | None = None) -> str:
    """Store the user's verbatim prompt text for later use.

    This function currently does nothing but may be extended in the future
    to store the prompt text for inclusion in commit messages.

    Args:
        user_text: The user's original prompt verbatim
        chat_id: The unique ID of the current chat session

    Returns:
        A confirmation message
    """
    try:
        logging.info(f"Received user prompt for chat ID {chat_id}: {user_text}")
        # For now, this is just a placeholder that returns a confirmation
        # In the future, this might store the text for use in commit messages
        return "User prompt received"
    except Exception as e:
        logging.warning(f"Exception suppressed in user_prompt: {e!s}", exc_info=True)
        return f"Error processing user prompt: {e!s}"
