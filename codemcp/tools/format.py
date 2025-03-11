#!/usr/bin/env python3

import logging
from typing import Optional, List

from .code_command import get_command_from_config, run_code_command

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
    return get_command_from_config(project_dir, "format")


def format_code(project_dir: str) -> str:
    """Format code using the command configured in codemcp.toml.

    Args:
        project_dir: The directory path containing the codemcp.toml file

    Returns:
        A string containing the result of the format operation
    """
    format_command = _get_format_command(project_dir)
    return run_code_command(
        project_dir, 
        "formatting", 
        format_command, 
        "Auto-commit formatting changes"
    )