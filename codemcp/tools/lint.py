#!/usr/bin/env python3

import logging
import os
import subprocess
from pathlib import Path
import tomli
from typing import List, Optional

from ..common import normalize_file_path
from ..git import is_git_repository, commit_changes
from ..shell import run_command

__all__ = [
    "lint_code",
]


def _get_lint_command(project_dir: str) -> Optional[List[str]]:
    """Get the lint command from the codemcp.toml file.

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

        if "commands" in config and "lint" in config["commands"]:
            return config["commands"]["lint"]

        return None
    except Exception as e:
        logging.error(f"Error loading lint command: {e}")
        return None


def _check_for_changes(project_dir: str) -> bool:
    """Check if linting made any changes to the code.

    Args:
        project_dir: The directory path to check

    Returns:
        True if changes were detected, False otherwise
    """
    try:
        # Get the git repository root for reliable status checking
        try:
            repo_root = run_command(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=project_dir,
                check=True,
                capture_output=True,
                text=True,
            ).stdout.strip()

            # Use the repo root as working directory for git commands
            git_cwd = repo_root
        except (subprocess.SubprocessError, OSError) as e:
            logging.error(f"Error getting git repository root: {e}")
            # Fall back to the project directory
            git_cwd = project_dir

        # Check if working directory has uncommitted changes
        status_result = run_command(
            ["git", "status", "--porcelain"],
            cwd=git_cwd,
            check=True,
            capture_output=True,
            text=True,
        )

        # If status output is not empty, there are changes
        return bool(status_result.stdout.strip())
    except Exception as e:
        logging.error(f"Error checking for git changes: {e}")
        return False


def lint_code(project_dir: str) -> str:
    """Lint code using the command configured in codemcp.toml.

    Args:
        project_dir: The directory path containing the codemcp.toml file

    Returns:
        A string containing the result of the lint operation
    """
    try:
        full_dir_path = normalize_file_path(project_dir)

        if not os.path.exists(full_dir_path):
            return f"Error: Directory does not exist: {project_dir}"

        if not os.path.isdir(full_dir_path):
            return f"Error: Path is not a directory: {project_dir}"

        lint_command = _get_lint_command(full_dir_path)

        if not lint_command:
            return "Error: No lint command configured in codemcp.toml"

        # Check if directory is in a git repository
        is_git_repo = is_git_repository(full_dir_path)

        # If it's a git repo, commit any pending changes before linting
        if is_git_repo:
            # Commit any pending changes before running linter
            logging.info("Committing any pending changes before linting")
            commit_result = commit_changes(
                full_dir_path, "Snapshot before auto-linting"
            )
            if not commit_result[0]:
                logging.warning(f"Failed to commit pending changes: {commit_result[1]}")

        # Run the lint command
        try:
            result = run_command(
                lint_command,
                cwd=full_dir_path,
                check=True,
                capture_output=True,
                text=True,
            )

            # Additional logging is already done by run_command

            # If it's a git repo, commit any changes made by linter
            if is_git_repo:
                has_changes = _check_for_changes(full_dir_path)
                if has_changes:
                    logging.info("Changes detected after linting, committing")
                    success, commit_message = commit_changes(
                        full_dir_path, "Auto-commit linting changes"
                    )

                    if success:
                        return f"Code linting successful and changes committed:\n{result.stdout}"
                    else:
                        logging.warning(
                            f"Failed to commit linting changes: {commit_message}"
                        )
                        return f"Code linting successful but failed to commit changes:\n{result.stdout}\nCommit error: {commit_message}"

            return f"Code linting successful:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            error_msg = (
                f"Lint command failed with exit code {e.returncode}:\n{e.stderr}"
            )
            # Note: run_command already logs the command and stderr at debug level
            # We just need to log the error summary at error level
            logging.error(f"Lint command failed with exit code {e.returncode}")
            return f"Error: {error_msg}"

    except Exception as e:
        error_msg = f"Error linting code: {e}"
        logging.error(error_msg)
        return f"Error: {error_msg}"