#!/usr/bin/env python3

import os
import sys
import logging
from typing import Optional, Tuple

from ..git import commit_changes, commit_pending_changes


def detect_file_encoding(file_path: str) -> str:
    """Detect the encoding of a file.

    Args:
        file_path: The path to the file

    Returns:
        The detected encoding, defaulting to 'utf-8'
    """
    # Simple implementation - in a real-world scenario, you might use chardet or similar
    try:
        # Try to read the file with utf-8 encoding
        with open(file_path, "r", encoding="utf-8") as f:
            f.read()
        return "utf-8"
    except UnicodeDecodeError:
        # If utf-8 fails, default to binary mode
        return "latin-1"  # A safe fallback


def detect_line_endings(file_path: str) -> str:
    """Detect the line endings of a file.

    Args:
        file_path: The path to the file

    Returns:
        The detected line endings ('\n' or '\r\n')
    """
    try:
        with open(file_path, "rb") as f:
            content = f.read()
        if b"\r\n" in content:
            return "\r\n"
        return "\n"
    except Exception:
        return os.linesep


def detect_repo_line_endings(directory: str) -> str:
    """Detect the line endings used in a repository.

    Args:
        directory: The repository directory

    Returns:
        The detected line endings ('\n' or '\r\n')
    """
    # Default to system line endings
    return os.linesep


def write_text_content(
    file_path: str, content: str, encoding: str = "utf-8", line_endings: str = None
) -> None:
    """Write text content to a file with specified encoding and line endings.

    Args:
        file_path: The path to the file
        content: The content to write
        encoding: The encoding to use
        line_endings: The line endings to use
    """
    if line_endings and line_endings != "\n":
        # Normalize to \n first, then replace with desired line endings
        content = content.replace("\r\n", "\n").replace("\n", line_endings)

    with open(file_path, "w", encoding=encoding) as f:
        f.write(content)


def write_file_content(file_path: str, content: str, description: str = "") -> str:
    """Write content to a file.

    Args:
        file_path: The absolute path to the file to write
        content: The content to write to the file
        description: Short description of the change

    Returns:
        A success message or an error message
    """
    try:
        if not os.path.isabs(file_path):
            return f"Error: File path must be absolute, not relative: {file_path}"

        # First commit any pending changes
        commit_success, commit_message = commit_pending_changes(file_path)
        if not commit_success:
            logging.debug(f"Failed to commit pending changes: {commit_message}")
        else:
            logging.debug(f"Pending changes status: {commit_message}")

        # Get directory and ensure it exists
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            # Create directory instead of returning an error
            os.makedirs(directory, exist_ok=True)

        # Determine encoding and line endings
        old_file_exists = os.path.exists(file_path)
        encoding = detect_file_encoding(file_path) if old_file_exists else "utf-8"

        if old_file_exists:
            line_endings = detect_line_endings(file_path)
        else:
            line_endings = detect_repo_line_endings(directory)

        # Write the content with proper encoding and line endings
        write_text_content(file_path, content, encoding, line_endings)

        # Commit the changes
        git_message = ""
        success, message = commit_changes(file_path, description)
        if success:
            git_message = f"\nChanges committed to git: {description}"
        else:
            git_message = f"\nFailed to commit changes to git: {message}"

        return f"Successfully wrote to {file_path}{git_message}"
    except Exception as e:
        return f"Error writing file: {str(e)}"