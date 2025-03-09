#!/usr/bin/env python3

import os
from typing import Optional

def write_file_content(file_path: str, content: str) -> str:
    """Write content to a file.

    Args:
        file_path: The absolute path to the file to write
        content: The content to write to the file

    Returns:
        A success message or an error message
    """
    try:
        if not os.path.isabs(file_path):
            return f"Error: File path must be absolute, not relative: {file_path}"

        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            return f"Error: Directory does not exist: {directory}"

        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)

        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"
