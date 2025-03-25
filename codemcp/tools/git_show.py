#!/usr/bin/env python3

import logging
import shlex
from typing import Any

from ..common import normalize_file_path
from ..git import is_git_repository
from ..shell import run_command

__all__ = [
    "git_show",
    "render_result_for_assistant",
    "TOOL_NAME_FOR_PROMPT",
    "DESCRIPTION",
]

TOOL_NAME_FOR_PROMPT = "GitShow"
DESCRIPTION = """
Shows various types of objects (commits, tags, trees, blobs) using git show.
This tool is read-only and safe to use with any arguments.
The arguments parameter should be a string and will be interpreted as space-separated
arguments using shell-style tokenization (spaces separate arguments, quotes can be used
for arguments containing spaces, etc.).

Example:
  git show  # Show the most recent commit
  git show a1b2c3d  # Show a specific commit by hash
  git show HEAD~3  # Show the commit 3 before HEAD
  git show v1.0  # Show a tag
  git show HEAD:path/to/file  # Show a file from a specific commit
"""


async def git_show(
    arguments: str | None = None,
    path: str | None = None,
    chat_id: str | None = None,
    signal=None,
) -> dict[str, Any]:
    """Execute git show with the provided arguments.

    Args:
        arguments: Optional arguments to pass to git show as a string
        path: The directory to execute the command in (must be in a git repository)
        chat_id: The unique ID of the current chat session
        signal: Optional abort signal to terminate the subprocess

    Returns:
        A dictionary with git show output
    """

    if path is None:
        raise ValueError("Path must be provided for git show")

    # Normalize the directory path
    absolute_path = normalize_file_path(path)

    # Verify this is a git repository
    if not await is_git_repository(absolute_path):
        raise ValueError(f"The provided path is not in a git repository: {path}")

    # Build command
    cmd = ["git", "show"]

    # Add additional arguments if provided
    if arguments:
        parsed_args = shlex.split(arguments)
        cmd.extend(parsed_args)

    logging.debug(f"Executing git show command: {' '.join(cmd)}")

    try:
        # Execute git show command asynchronously
        result = await run_command(
            cmd=cmd,
            cwd=absolute_path,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception if git show fails
        )

        # Process results
        if result.returncode != 0:
            logging.error(
                f"git show failed with exit code {result.returncode}: {result.stderr}"
            )
            error_message = f"Error: {result.stderr}"
            return {
                "output": error_message,
                "resultForAssistant": error_message,
            }

        # Prepare output
        output = {
            "output": result.stdout,
        }

        # Add formatted result for assistant
        output["resultForAssistant"] = render_result_for_assistant(output)

        return output
    except Exception as e:
        logging.exception(f"Error executing git show: {e!s}")
        error_message = f"Error executing git show: {e!s}"
        return {
            "output": error_message,
            "resultForAssistant": error_message,
        }


def render_result_for_assistant(output: dict[str, Any]) -> str:
    """Render the results in a format suitable for the assistant.

    Args:
        output: The git show output dictionary

    Returns:
        A formatted string representation of the results
    """
    return output.get("output", "")
