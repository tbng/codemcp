#!/usr/bin/env python3

import logging
import os
import subprocess

import toml


def get_git_base_dir(file_path: str) -> str | None:
    """Get the base directory of the git repository containing the file.

    Args:
        file_path: The path to the file or directory

    Returns:
        The base directory of the git repository, or None if not in a git repository

    """
    try:
        # Get the directory containing the file - handle non-existent files
        if os.path.exists(file_path):
            directory = (
                os.path.dirname(file_path) if os.path.isfile(file_path) else file_path
            )
        else:
            # For non-existent files, use the parent directory
            directory = os.path.dirname(file_path)
            # If directory doesn't exist either, stop here
            if not os.path.exists(directory):
                logging.debug(f"Directory doesn't exist: {directory}")
                return None

        # Run git command to get the top-level directory of the repository
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )

        # Log command output and return the path
        git_base_dir = result.stdout.strip()
        logging.debug(f"Git base directory: {git_base_dir}")
        return git_base_dir
    except (subprocess.SubprocessError, OSError) as e:
        logging.debug(f"Error finding git base directory: {e!s}")
        return None


def check_edit_permission(file_path: str) -> tuple[bool, str]:
    """Check if editing the file is permitted based on the presence of codemcp.toml
    in the git repository's root directory.

    Args:
        file_path: The path to the file to edit

    Returns:
        A tuple of (is_permitted, message)

    """
    # Get the git base directory
    git_base_dir = get_git_base_dir(file_path)

    # If not in a git repository, deny access
    if not git_base_dir:
        return False, "File is not in a git repository. Permission denied."

    # Check for codemcp.toml in the git base directory
    config_path = os.path.join(git_base_dir, "codemcp.toml")
    if not os.path.exists(config_path):
        return False, (
            "Permission denied: codemcp.toml file not found in the git repository root. "
            "Please create a codemcp.toml file in the root directory of your project "
            "to enable editing files with codemcp."
        )

    # Optionally, verify the content of the codemcp.toml file
    try:
        toml.load(config_path)
        # You can add more sophisticated permission checks here based on the config
        # For example, check for allowed_directories, deny_patterns, etc.
        return True, "Permission granted."
    except Exception as e:
        return False, f"Error parsing codemcp.toml file: {e!s}"
