#!/usr/bin/env python3

import os
from typing import Optional

from ..common import get_edit_snippet

def edit_file_content(file_path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing old_string with new_string.

    Args:
        file_path: The absolute path to the file to edit
        old_string: The text to replace
        new_string: The new text to replace old_string with

    Returns:
        A success message or an error message
    """
    try:
        if not os.path.isabs(file_path):
            return f"Error: File path must be absolute, not relative: {file_path}"

        # Handle creating a new file
        if not old_string and not os.path.exists(file_path):
            directory = os.path.dirname(file_path)
            os.makedirs(directory, exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_string)
            return f"Successfully created {file_path}"

        # Handle existing file validation
        if not os.path.exists(file_path):
            return f"Error: File does not exist: {file_path}"

        if os.path.isdir(file_path):
            return f"Error: Path is a directory, not a file: {file_path}"

        # No changes to make
        if old_string == new_string:
            return "No changes to make: old_string and new_string are exactly the same."

        # Read the original file
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()

        # Check if old_string exists in the file
        if old_string and old_string not in content:
            return "Error: The provided text to replace was not found in the file. Make sure it matches exactly, including whitespace and indentation."

        # Check for uniqueness of old_string
        if old_string and content.count(old_string) > 1:
            return "Error: The provided text to replace appears multiple times in the file. Please provide more context to uniquely identify the instance to replace."

        # Create a snippet of the changes for the response
        original_content = content
        new_content = content.replace(old_string, new_string, 1)

        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)

        # Generate a snippet of the edited file to show in the response
        snippet = get_edit_snippet(original_content, old_string, new_string)

        return f"Successfully edited {file_path}\n\nHere's a snippet of the edited file:\n{snippet}"
    except Exception as e:
        return f"Error editing file: {str(e)}"
