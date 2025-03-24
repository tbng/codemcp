#!/usr/bin/env python3

import logging

__all__ = [
    "think",
]


async def think(thought: str, chat_id: str | None = None) -> str:
    """Use this tool to think about something without obtaining new information or changing the database.

    Args:
        thought: The thought to log
        chat_id: The unique ID of the current chat session

    Returns:
        A confirmation message that the thought was logged
    """
    # Log the thought but don't actually do anything with it
    logging.info(f"[{chat_id}] Thought: {thought}")

    # Return a simple confirmation message
    return f"Thought logged: {thought}"
