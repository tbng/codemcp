#!/usr/bin/env python3

import logging
import os
import subprocess
from typing import List, Optional

import tomli

from ..common import normalize_file_path
from ..shell import run_command

__all__ = [
    "run_tests",
]


def _get_test_command(project_dir: str) -> Optional[List[str]]:
    """Get the test command from the codemcp.toml file.

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

        if "commands" in config and "test" in config["commands"]:
            return config["commands"]["test"]

        return None
    except Exception as e:
        logging.error(f"Error loading test command: {e}")
        return None


def run_tests(project_dir: str, test_selector: Optional[str] = None) -> str:
    """Run tests using the command configured in codemcp.toml.

    Args:
        project_dir: The directory path containing the codemcp.toml file
        test_selector: Optional selector to run specific tests

    Returns:
        A string containing the result of the test operation
    """
    try:
        full_dir_path = normalize_file_path(project_dir)

        if not os.path.exists(full_dir_path):
            return f"Error: Directory does not exist: {project_dir}"

        if not os.path.isdir(full_dir_path):
            return f"Error: Path is not a directory: {project_dir}"

        test_command = _get_test_command(full_dir_path)

        if not test_command:
            return "Error: No test command configured in codemcp.toml"

        # Create a command with the optional test selector
        command = test_command.copy()
        if test_selector:
            command.append(test_selector)

        # Run the test command
        try:
            result = run_command(
                command,
                cwd=full_dir_path,
                check=True,
                capture_output=True,
                text=True,
            )

            return f"Tests completed successfully:\n{result.stdout}"
        except subprocess.CalledProcessError as e:
            error_msg = (
                f"Test command failed with exit code {e.returncode}:\n{e.stderr}"
            )
            logging.error(f"Test command failed with exit code {e.returncode}")
            return f"Tests failed:\n{e.stdout}\n{e.stderr}"

    except Exception as e:
        error_msg = f"Error running tests: {e}"
        logging.error(error_msg)
        return f"Error: {error_msg}"
