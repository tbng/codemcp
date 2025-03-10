#!/usr/bin/env python3

import os
from pathlib import Path
from typing import Optional

import tomli

from ..common import normalize_file_path


def init_project(directory: str) -> str:
    """
    Initialize a project by reading the codemcp.toml TOML file and returning
    a combined system prompt.

    Args:
        directory: The directory path containing the codemcp.toml file

    Returns:
        A string containing the system prompt plus any global_prompt from the config
    """
    try:
        # Normalize the directory path
        full_dir_path = normalize_file_path(directory)

        # Validate the directory path
        if not os.path.exists(full_dir_path):
            return f"Error: Directory does not exist: {directory}"

        if not os.path.isdir(full_dir_path):
            return f"Error: Path is not a directory: {directory}"

        # Build path to codemcp.toml file
        rules_file_path = os.path.join(full_dir_path, "codemcp.toml")

        # Default system prompt
        system_prompt = "Do NOT attempt to run tests, let the user run them."
        global_prompt = ""

        # Check if codemcp.toml file exists
        if os.path.exists(rules_file_path):
            try:
                with open(rules_file_path, "rb") as f:
                    rules_config = tomli.load(f)
                
                # Extract global_prompt if it exists
                if "global_prompt" in rules_config:
                    global_prompt = rules_config["global_prompt"]
            except Exception as e:
                return f"Error reading codemcp.toml file: {str(e)}"

        # Combine system prompt and global prompt
        combined_prompt = system_prompt
        if global_prompt:
            combined_prompt += "\n\n" + global_prompt

        return combined_prompt
    except Exception as e:
        return f"Error initializing project: {str(e)}"
