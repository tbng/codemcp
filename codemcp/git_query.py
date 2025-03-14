#!/usr/bin/env python3

import inspect
import logging
import os
import re
import subprocess

from .shell import run_command

__all__ = [
    "get_head_commit_message",
    "get_head_commit_hash",
    "get_head_commit_chat_id",
    "get_repository_root",
    "is_git_repository",
    "get_ref_commit_chat_id",
]

log = logging.getLogger(__name__)


async def get_head_commit_message(directory: str) -> str | None:
    """Get the full commit message from HEAD.

    Args:
        directory: The directory to check

    Returns:
        The commit message if available, None otherwise
    """
    try:
        # Check if HEAD exists
        result = await run_command(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=directory,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # No commits yet
            return None

        # Get the commit message
        result = await run_command(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()
    except Exception as e:
        logging.warning(
            f"Exception when getting HEAD commit message: {e!s}", exc_info=True
        )
        return None


async def get_head_commit_hash(directory: str, short: bool = True) -> str | None:
    """Get the commit hash from HEAD.

    Args:
        directory: The directory to check
        short: Whether to get short hash (default) or full hash

    Returns:
        The commit hash if available, None otherwise
    """
    try:
        # Check if HEAD exists
        result = await run_command(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=directory,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # No commits yet
            return None

        # Get the commit hash (short or full)
        cmd = ["git", "rev-parse"]
        if short:
            cmd.append("--short")
        cmd.append("HEAD")

        result = await run_command(
            cmd,
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()
    except Exception as e:
        logging.warning(
            f"Exception when getting HEAD commit hash: {e!s}", exc_info=True
        )
        return None


async def get_head_commit_chat_id(directory: str) -> str | None:
    """Get the chat ID from the HEAD commit's message.

    Args:
        directory: The directory to check

    Returns:
        The chat ID if found, None otherwise
    """
    try:
        commit_message = await get_head_commit_message(directory)
        if not commit_message:
            return None

        # Use regex to find the last occurrence of codemcp-id: XXX
        # The pattern looks for "codemcp-id: " followed by any characters up to a newline or end of string
        matches = re.findall(r"codemcp-id:\s*([^\n]*)", commit_message)

        # Return the last match if any matches found
        if matches:
            return matches[-1].strip()
        return None
    except Exception as e:
        logging.warning(
            f"Exception when getting HEAD commit chat ID: {e!s}", exc_info=True
        )
        return None


async def get_repository_root(path: str) -> str:
    """Get the root directory of the Git repository containing the path.

    Args:
        path: The file path to get the repository root for

    Returns:
        The absolute path to the repository root

    Raises:
        ValueError: If the path is not in a Git repository
    """
    try:
        # Get the directory containing the file or use the path itself if it's a directory
        directory = os.path.dirname(path) if os.path.isfile(path) else path

        # Get the absolute path to ensure consistency
        directory = os.path.abspath(directory)

        # Get the absolute path of the current module to identify codemcp repo
        current_module_dir = os.path.dirname(
            os.path.abspath(inspect.getfile(inspect.currentframe()))
        )
        codemcp_repo_path = os.path.abspath(os.path.join(current_module_dir, ".."))

        # Get the repository root
        result = await run_command(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        repo_root = result.stdout.strip()

        # Warn if operating in the codemcp repository (development issue)
        if os.environ.get("CODEMCP_DEBUG") and repo_root == codemcp_repo_path:
            logging.warning(f"Operating in codemcp repository: {repo_root}")

        return repo_root

        return repo_root
    except (subprocess.SubprocessError, OSError) as e:
        raise ValueError(f"Path is not in a git repository: {str(e)}")


async def is_git_repository(path: str) -> bool:
    """Check if the path is within a Git repository.

    Args:
        path: The file path to check

    Returns:
        True if path is in a Git repository, False otherwise

    """
    try:
        # Get the directory containing the file or use the path itself if it's a directory
        directory = os.path.dirname(path) if os.path.isfile(path) else path

        # Get the absolute path to ensure consistency
        directory = os.path.abspath(directory)

        # Run git command to verify this is a git repository
        await run_command(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        # Also get the repository root to use for all git operations
        try:
            await run_command(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )

            # Store the repository root in a global or class variable if needed
            # This could be used to ensure all git operations use the same root

            return True
        except (subprocess.SubprocessError, OSError):
            # If we can't get the repo root, it's not a proper git repository
            return False
    except (subprocess.SubprocessError, OSError):
        return False


async def get_ref_commit_chat_id(directory: str, ref_name: str) -> str | None:
    """Get the chat ID from a specific reference's commit message.

    Args:
        directory: The directory to check
        ref_name: The reference name to check

    Returns:
        The chat ID if found, None otherwise
    """
    try:
        # Check if the reference exists
        result = await run_command(
            ["git", "show-ref", "--verify", ref_name],
            cwd=directory,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # Reference doesn't exist
            return None

        # Get the commit message from the reference
        message_result = await run_command(
            ["git", "log", "-1", "--pretty=%B", ref_name],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )
        commit_message = message_result.stdout.strip()

        # Use regex to find the last occurrence of codemcp-id: XXX
        # The pattern looks for "codemcp-id: " followed by any characters up to a newline or end of string
        matches = re.findall(r"codemcp-id:\s*([^\n]*)", commit_message)

        # Return the last match if any matches found
        if matches:
            return matches[-1].strip()
        return None
    except Exception as e:
        logging.warning(
            f"Exception when getting reference commit chat ID: {e!s}", exc_info=True
        )
        return None
