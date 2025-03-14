#!/usr/bin/env python3

import os
from typing import List, Optional

from .code_command import get_command_from_config, run_code_command

__all__ = [
    "run_command",
]


async def run_command(
    project_dir: str,
    command: str,
    arguments: Optional[List[str]] = None,
    chat_id: str = None,
) -> str:
    """Run a command that is configured in codemcp.toml.

    Args:
        project_dir: The directory path containing the codemcp.toml file
        command: The type of command to run (e.g., "format", "lint", "test")
        arguments: Optional list of arguments to pass to the command
        chat_id: The unique ID of the current chat session

    Returns:
        A string containing the result of the command operation
    """
    import logging

    # Get the normalized absolute path to ensure we're operating in the correct directory
    normalized_project_dir = os.path.abspath(project_dir)

    # Get the absolute path of the codemcp repository from module location
    import inspect

    current_module_dir = os.path.dirname(
        os.path.abspath(inspect.getfile(inspect.currentframe()))
    )
    codemcp_repo_path = os.path.abspath(os.path.join(current_module_dir, "..", ".."))

    # Add a safeguard to prevent using the codemcp repository directory for commands
    if normalized_project_dir == codemcp_repo_path:
        logging.error(
            f"Attempted to run command in codemcp repository directory: {normalized_project_dir}"
        )
        return (
            f"Error: Cannot run commands directly in the codemcp repository directory. "
            f"The command '{command}' must be run in a project directory."
        )

    command_list = get_command_from_config(project_dir, command)

    # If arguments are provided, extend the command with them
    if arguments and command_list:
        command_list = command_list.copy()
        command_list.extend(arguments)

    # Ensure we log what's happening
    logging.info(
        f"Running {command} command in directory {normalized_project_dir} with arguments: {arguments}"
    )

    return await run_code_command(
        project_dir, command, command_list, f"Auto-commit {command} changes", chat_id
    )
