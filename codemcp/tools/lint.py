#!/usr/bin/env python3

from typing import List, Optional

from .code_command import get_command_from_config, run_code_command

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
    return get_command_from_config(project_dir, "lint")


def lint_code(project_dir: str) -> str:
    """Lint code using the command configured in codemcp.toml.

    Args:
        project_dir: The directory path containing the codemcp.toml file

    Returns:
        A string containing the result of the lint operation
    """
    lint_command = _get_lint_command(project_dir)
    return run_code_command(
        project_dir, "linting", lint_command, "Auto-commit linting changes"
    )
