#!/usr/bin/env python3

import logging
import os
import re

from ..common import normalize_file_path
from ..git import commit_changes, get_repository_root
from ..shell import run_command

__all__ = [
    "rm_file",
]


async def rm_file(
    path: str,
    description: str,
    chat_id: str = None,
) -> str:
    """Remove a file using git rm.

    Args:
        path: The path to the file to remove (can be absolute or relative to repository root)
        description: Short description of why the file is being removed
        chat_id: The unique ID of the current chat session

    Returns:
        A string containing the result of the removal operation
    """
    # Use the directory from the path as our starting point
    file_path = normalize_file_path(path)
    dir_path = os.path.dirname(file_path) if os.path.dirname(file_path) else "."

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File does not exist: {path}")

    if not os.path.isfile(file_path):
        raise ValueError(f"Path is not a file: {path}")

    # Get git repository root
    git_root = await get_repository_root(dir_path)
    # Fix git root path - ensure it's normalized the same way as our file path
    git_root = normalize_file_path(git_root)

    # Function to normalize paths for comparison
    def normalize_path_for_comparison(path):
        # Convert to absolute path
        path = os.path.abspath(path)
        # Handle symbolic links
        if os.path.islink(path):
            path = os.path.realpath(path)
        # Normalize path separators
        path = path.replace("\\", "/")
        # Remove trailing slash
        path = path.rstrip("/")
        # Handle macOS /private/tmp vs /tmp
        path = re.sub(r"^/private(/tmp/.*)", r"\1", path)
        return path

    # Normalize paths for comparison
    norm_file_path = normalize_path_for_comparison(file_path)
    norm_git_root = normalize_path_for_comparison(git_root)

    # Check if file is in the git repo
    if not norm_file_path.startswith(norm_git_root):
        msg = f"Path {file_path} is not within the git repository at {git_root}"
        logging.error(msg)
        raise ValueError(msg)

    # Get the relative path
    os.path.relpath(file_path, git_root)

    # Run git rm on the file - just use the basename to be safe
    file_basename = os.path.basename(file_path)
    logging.info(f"Running git rm on file: {file_basename}")

    # Before running git rm, we need to change to the directory containing the file
    # to avoid path issues
    file_dir = os.path.dirname(file_path)
    if not file_dir:
        file_dir = git_root

    # Check if the file is tracked by git
    await run_command(
        ["git", "ls-files", "--error-unmatch", file_basename],
        cwd=file_dir,
        check=True,
        capture_output=True,
        text=True,
    )

    # If we get here, the file is tracked by git, so we can remove it
    await run_command(
        ["git", "rm", file_basename],
        cwd=file_dir,
        check=True,
        capture_output=True,
        text=True,
    )

    # Commit the changes
    logging.info(f"Committing removal of file: {file_basename}")
    success, commit_message = await commit_changes(
        git_root,
        f"Remove {file_basename}: {description}",
        chat_id,
        commit_all=False,  # No need for commit_all since git rm already stages the change
    )

    if success:
        return f"Successfully removed file {file_basename}."
    else:
        return (
            f"File {file_basename} was removed but failed to commit: {commit_message}"
        )
