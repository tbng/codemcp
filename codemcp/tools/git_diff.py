#!/usr/bin/env python3

import logging
import shlex
import time
from typing import Any

from ..common import normalize_file_path
from ..git import is_git_repository
from ..shell import run_command

__all__ = [
    "git_diff",
    "render_result_for_assistant",
    "TOOL_NAME_FOR_PROMPT",
    "DESCRIPTION",
]

TOOL_NAME_FOR_PROMPT = "GitDiff"
DESCRIPTION = """
Shows differences between commits, commit and working tree, etc. using git diff.
This tool is read-only and safe to use with any arguments.
The arguments parameter should be a string and will be interpreted as space-separated
arguments using shell-style tokenization (spaces separate arguments, quotes can be used
for arguments containing spaces, etc.).

Example:
  git diff  # Show changes between working directory and index
  git diff HEAD~1  # Show changes between current commit and previous commit
  git diff branch1 branch2  # Show differences between two branches
  git diff --stat  # Show summary of changes instead of full diff
"""


async def git_diff(
    arguments: str | None = None,
    path: str | None = None,
    chat_id: str | None = None,
    signal=None,
) -> dict[str, Any]:
    """Execute git diff with the provided arguments.

    Args:
        arguments: Optional arguments to pass to git diff as a string
        path: The directory to execute the command in (must be in a git repository)
        chat_id: The unique ID of the current chat session
        signal: Optional abort signal to terminate the subprocess

    Returns:
        A dictionary with execution stats and git diff output
    """
    start_time = time.time()

    if path is None:
        raise ValueError("Path must be provided for git diff")

    # Normalize the directory path
    absolute_path = normalize_file_path(path)

    # Verify this is a git repository
    if not await is_git_repository(absolute_path):
        raise ValueError(f"The provided path is not in a git repository: {path}")

    # Build command
    cmd = ["git", "diff"]

    # Add additional arguments if provided
    if arguments:
        parsed_args = shlex.split(arguments)
        cmd.extend(parsed_args)

    logging.debug(f"Executing git diff command: {' '.join(cmd)}")

    try:
        # Execute git diff command asynchronously
        result = await run_command(
            cmd=cmd,
            cwd=absolute_path,
            capture_output=True,
            text=True,
            check=False,  # Don't raise exception if git diff fails
        )

        # Process results
        if result.returncode != 0:
            logging.error(
                f"git diff failed with exit code {result.returncode}: {result.stderr}"
            )
            error_message = f"Error: {result.stderr}"
            return {
                "output": error_message,
                "durationMs": int((time.time() - start_time) * 1000),
                "resultForAssistant": error_message,
            }

        # Calculate execution time
        execution_time = int(
            (time.time() - start_time) * 1000
        )  # Convert to milliseconds

        # Prepare output
        output = {
            "output": result.stdout,
            "durationMs": execution_time,
        }

        # Add formatted result for assistant
        output["resultForAssistant"] = render_result_for_assistant(output)

        return output
    except Exception as e:
        logging.exception(f"Error executing git diff: {e!s}")
        error_message = f"Error executing git diff: {e!s}"
        return {
            "output": error_message,
            "durationMs": int((time.time() - start_time) * 1000),
            "resultForAssistant": error_message,
        }


def render_result_for_assistant(output: dict[str, Any]) -> str:
    """Render the results in a format suitable for the assistant.

    Args:
        output: The git diff output dictionary

    Returns:
        A formatted string representation of the results
    """
    return output.get("output", "")
