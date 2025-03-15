#!/usr/bin/env python3

"""
Module for handling custom slash commands in codemcp.

Slash commands can be defined by users by adding Markdown files to:
- .claude/commands/ (project-specific)
- ~/.claude/commands/ (global)

When a matching slash command is detected in the user's prompt, the contents
of the corresponding Markdown file will be returned.
"""

import logging
import re
from pathlib import Path
from typing import Dict, Optional, Tuple

__all__ = [
    "get_slash_command",
    "find_slash_command",
    "load_slash_commands",
]


def get_commands_directories() -> Tuple[Path, Path]:
    """Get the directories where custom slash commands are stored.

    Returns:
        Tuple of (project_commands_dir, global_commands_dir)
    """
    # Project-specific commands directory (.claude/commands/)
    project_commands_dir = Path(".claude/commands")

    # Global commands directory (~/.claude/commands/)
    global_commands_dir = Path.home() / ".claude/commands"

    return project_commands_dir, global_commands_dir


def load_slash_commands() -> Dict[str, str]:
    """Load all available slash commands from the commands directories.

    Returns:
        Dict mapping command names to their content.
    """
    commands = {}
    project_dir, global_dir = get_commands_directories()

    # Process global commands first, so project commands can override them
    for commands_dir in [global_dir, project_dir]:
        if not commands_dir.exists() or not commands_dir.is_dir():
            continue

        for file_path in commands_dir.glob("*.md"):
            command_name = (
                file_path.stem
            )  # Use the filename (without extension) as the command name

            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                commands[command_name] = content
                logging.debug(f"Loaded slash command: /{command_name}")
            except Exception as e:
                logging.warning(f"Error loading slash command from {file_path}: {e}")

    return commands


def find_slash_command(text: str) -> Optional[str]:
    """Find a slash command in the given text.

    Args:
        text: The text to search for slash commands

    Returns:
        The name of the first slash command found (without the slash), or None if not found
    """
    # Look for patterns like /command or /command-name at the beginning of a line or after a space
    pattern = r"(?:^|\s)\/([a-zA-Z0-9_-]+)"
    match = re.search(pattern, text)

    if match:
        return match.group(1)
    return None


def get_slash_command(text: str) -> Optional[str]:
    """Check if the text contains a slash command and return its content if found.

    Args:
        text: The text to check for slash commands

    Returns:
        The content of the matched slash command, or None if no command is found
    """
    command_name = find_slash_command(text)
    if not command_name:
        return None

    commands = load_slash_commands()
    return commands.get(command_name)
