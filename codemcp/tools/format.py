#!/usr/bin/env python3

import logging
import os
import subprocess
from pathlib import Path
import tomli
from typing import List, Optional

from ..common import normalize_file_path
from ..git import is_git_repository, commit_changes

__all__ = [
    "format_code",
]


def _get_format_command(project_dir: str) -> Optional[List[str]]:
    """Get the format command from the codemcp.toml file.

    Args:
        project_dir: The directory path containing the codemcp.toml file

    Returns:
        A list of command parts if configured, None otherwise
    """
    try:
        full_dir_path = normalize_file_path(project_dir)
        config_path = os.path.join(full_dir_path, "codemcp.toml")

        if not os.path.exists(config_path):
            logging.warning(f"Config file not found: {config_path}")
            return None

        with open(config_path, "rb") as f:
            config = tomli.load(f)

        if "commands" in config and "format" in config["commands"]:
            return config["commands"]["format"]

        return None
    except Exception as e:
        logging.error(f"Error loading format command: {e}")
        return None


def _check_for_changes(project_dir: str) -> bool:
    """Check if formatting made any changes to the code.

    Args:
        project_dir: The directory path to check

    Returns:
        True if changes were detected, False otherwise
    """
    try:
        # Check if working directory has uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=project_dir,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )

        # If status output is not empty, there are changes
        return bool(status_result.stdout.strip())
    except Exception as e:
        logging.error(f"Error checking for git changes: {e}")
        return False


def format_code(project_dir: str) -> str:
    """Format code using the command configured in codemcp.toml.

    Args:
        project_dir: The directory path containing the codemcp.toml file

    Returns:
        A string containing the result of the format operation
    """
    try:
        full_dir_path = normalize_file_path(project_dir)

        if not os.path.exists(full_dir_path):
            return f"Error: Directory does not exist: {project_dir}"

        if not os.path.isdir(full_dir_path):
            return f"Error: Path is not a directory: {project_dir}"

        format_command = _get_format_command(full_dir_path)

        if not format_command:
            return "Error: No format command configured in codemcp.toml"

        # Check if directory is in a git repository
        is_git_repo = is_git_repository(full_dir_path)

        # If it's a git repo, check for changes before formatting
        had_changes_before = False
        if is_git_repo:
            had_changes_before = _check_for_changes(full_dir_path)

        # Run the format command
        try:
            result = subprocess.run(
                format_command,
                cwd=full_dir_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Log the command output
            logging.info(f"Format command output: {result.stdout}")
            if result.stderr:
                logging.warning(f"Format command stderr: {result.stderr}")

            # Check if there are changes after formatting
            if is_git_repo:
                has_changes_after = _check_for_changes(full_dir_path)

                # Only commit if new changes appeared after formatting
                if has_changes_after and (has_changes_after != had_changes_before):
                    logging.info("Changes detected after formatting, committing")
                    success, commit_message = commit_changes(
                        full_dir_path, "Auto-commit formatting changes"
                    )

                    if success:
                        return f"Code formatting successful and changes committed:\n{result.stdout}"
                    else:
                        logging.warning(
                            f"Failed to commit formatting changes: {commit_message}"
                        )
                        return f"Code formatting successful but failed to commit changes:\n{result.stdout}\nCommit error: {commit_message}"

            return f"Code formatting successful:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            error_msg = (
                f"Format command failed with exit code {e.returncode}:\n{e.stderr}"
            )
            logging.error(error_msg)
            return f"Error: {error_msg}"

    except Exception as e:
        error_msg = f"Error formatting code: {e}"
        logging.error(error_msg)
        return f"Error: {error_msg}"
