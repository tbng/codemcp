#!/usr/bin/env python3

import os
import stat
from typing import Optional, Dict, Tuple, List
import re

from ..common import get_edit_snippet

def detect_file_encoding(file_path: str) -> str:
    """Detect the encoding of a file.

    Args:
        file_path: The path to the file

    Returns:
        The encoding of the file, defaults to 'utf-8'
    """
    # Simple implementation - in a real app, would use chardet or similar
    return 'utf-8'

def detect_line_endings(file_path: str) -> str:
    """Detect the line endings of a file.

    Args:
        file_path: The path to the file

    Returns:
        'CRLF' or 'LF'
    """
    with open(file_path, 'rb') as f:
        content = f.read()
        if b'\r\n' in content:
            return 'CRLF'
        return 'LF'

def find_similar_file(file_path: str) -> Optional[str]:
    """Find a similar file with a different extension.

    Args:
        file_path: The path to the file

    Returns:
        The path to a similar file, or None if none found
    """
    # Simple implementation - in a real app, would check for files with different extensions
    directory = os.path.dirname(file_path)
    if not os.path.exists(directory):
        return None

    base_name = os.path.splitext(os.path.basename(file_path))[0]
    for f in os.listdir(directory):
        if f.startswith(base_name + '.') and f != os.path.basename(file_path):
            return os.path.join(directory, f)
    return None

def apply_edit(file_path: str, old_string: str, new_string: str) -> Tuple[List[Dict], str]:
    """Apply an edit to a file.

    Args:
        file_path: The path to the file
        old_string: The text to replace
        new_string: The text to replace it with

    Returns:
        A tuple of (patch, updated_file)
    """
    # Simple patch implementation - in a real app, would use a proper diff library
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding=detect_file_encoding(file_path)) as f:
            content = f.read()
    else:
        content = ''

    updated_file = content.replace(old_string, new_string, 1)

    # Create a simple patch structure
    # This is a simplified version of what the TS code does with the diff library
    patch = []
    if old_string != new_string:
        old_lines = old_string.split('\n')
        new_lines = new_string.split('\n')

        # Find the line number where the change occurs
        before_text = content.split(old_string)[0]
        line_num = before_text.count('\n')

        patch.append({
            'oldStart': line_num + 1,
            'oldLines': len(old_lines),
            'newStart': line_num + 1,
            'newLines': len(new_lines),
            'lines': [f"-{line}" for line in old_lines] + [f"+{line}" for line in new_lines]
        })

    return patch, updated_file

def write_text_content(file_path: str, content: str, encoding: str = 'utf-8', line_endings: str = 'LF') -> None:
    """Write text content to a file with the specified encoding and line endings.

    Args:
        file_path: The path to the file
        content: The content to write
        encoding: The encoding to use
        line_endings: The line endings to use ('CRLF' or 'LF')
    """
    # Normalize line endings
    if line_endings == 'CRLF':
        content = content.replace('\n', '\r\n')
    else:
        content = content.replace('\r\n', '\n')

    with open(file_path, 'w', encoding=encoding) as f:
        f.write(content)

def edit_file_content(file_path: str, old_string: str, new_string: str, read_file_timestamps: Optional[Dict[str, float]] = None) -> str:
    """Edit a file by replacing old_string with new_string.

    Args:
        file_path: The absolute path to the file to edit
        old_string: The text to replace
        new_string: The new text to replace old_string with
        read_file_timestamps: Dictionary mapping file paths to timestamps when they were last read

    Returns:
        A success message or an error message
    """
    try:
        # Convert to absolute path if needed
        full_file_path = file_path if os.path.isabs(file_path) else os.path.abspath(file_path)

        # Validate input
        if old_string == new_string:
            return "No changes to make: old_string and new_string are exactly the same."

        # Handle creating a new file
        if old_string == '' and os.path.exists(full_file_path):
            return "Cannot create new file - file already exists."

        # Handle creating a new file
        if old_string == '' and not os.path.exists(full_file_path):
            directory = os.path.dirname(full_file_path)
            os.makedirs(directory, exist_ok=True)
            write_text_content(full_file_path, new_string)
            return f"Successfully created {full_file_path}"

        # Check if file exists
        if not os.path.exists(full_file_path):
            # Try to find a similar file
            similar_file = find_similar_file(full_file_path)
            message = f"Error: File does not exist: {full_file_path}"
            if similar_file:
                message += f" Did you mean {similar_file}?"
            return message

        # Check if file is a Jupyter notebook
        if full_file_path.endswith('.ipynb'):
            return "Error: File is a Jupyter Notebook. Use the NotebookEditTool to edit this file."

        # Check if file has been read
        if read_file_timestamps and full_file_path not in read_file_timestamps:
            return "Error: File has not been read yet. Read it first before writing to it."

        # Check if file has been modified since read
        if read_file_timestamps and os.path.exists(full_file_path):
            last_write_time = os.stat(full_file_path).st_mtime
            if last_write_time > read_file_timestamps.get(full_file_path, 0):
                return "Error: File has been modified since read, either by the user or by a linter. Read it again before attempting to write it."

        # Detect encoding and line endings
        encoding = detect_file_encoding(full_file_path)
        line_endings = detect_line_endings(full_file_path)

        # Read the original file
        with open(full_file_path, 'r', encoding=encoding) as f:
            content = f.read()

        # Check if old_string exists in the file
        if old_string and old_string not in content:
            return "Error: String to replace not found in file."

        # Check for uniqueness of old_string
        if old_string and content.count(old_string) > 1:
            matches = content.count(old_string)
            return f"Error: Found {matches} matches of the string to replace. For safety, this tool only supports replacing exactly one occurrence at a time. Add more lines of context to your edit and try again."

        # Apply the edit
        patch, updated_file = apply_edit(full_file_path, old_string, new_string)

        # Create directory if it doesn't exist
        directory = os.path.dirname(full_file_path)
        os.makedirs(directory, exist_ok=True)

        # Write the modified content back to the file
        write_text_content(full_file_path, updated_file, encoding, line_endings)

        # Update read timestamp
        if read_file_timestamps is not None:
            read_file_timestamps[full_file_path] = os.stat(full_file_path).st_mtime

        # Generate a snippet of the edited file to show in the response
        snippet = get_edit_snippet(content, old_string, new_string)

        return f"Successfully edited {full_file_path}\n\nHere's a snippet of the edited file:\n{snippet}"
    except Exception as e:
        return f"Error editing file: {str(e)}"
