#!/usr/bin/env python3

import os
import sys
from typing import Optional, Dict, Any, List, Tuple
import base64
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context, Image

from .tools.read_file import read_file_content
from .tools.write_file import write_file_content
from .tools.edit_file import edit_file_content

# Initialize FastMCP server
mcp = FastMCP("deskaid")

@mcp.tool()
async def deskaid(ctx: Context, command: str, file_path: str, arg1: Optional[str] = None, arg2: Optional[str] = None) -> str:
    """
    This is a multipurpose tool that supports the following subcommands:

    ## ReadFile file_path offset? limit?

    Reads a file from the local filesystem. The file_path parameter must be an absolute path, not a relative path. By default, it reads up to ${MAX_LINES_TO_READ} lines starting from the beginning of the file. You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters. Any lines longer than ${MAX_LINE_LENGTH} characters will be truncated. For image files, the tool will display the image for you.

    ## WriteFile file_path content

    Write a file to the local filesystem. Overwrites the existing file if there is one.

    Before using this tool:

    1. Use the ReadFile tool to understand the file's contents and context

    2. Directory Verification (only applicable when creating new files):
       - Use the LS tool to verify the parent directory exists and is the correct location

    ## EditFile file_path old_string new_string

    This is a tool for editing files. For larger edits, use the Write tool to overwrite files.

    Before using this tool:

    1. Use the View tool to understand the file's contents and context

    2. Verify the directory path is correct (only applicable when creating new files):
       - Use the LS tool to verify the parent directory exists and is the correct location

    To make a file edit, provide the following:
    1. file_path: The absolute path to the file to modify (must be absolute, not relative)
    2. old_string: The text to replace (must be unique within the file, and must match the file contents exactly, including all whitespace and indentation)
    3. new_string: The edited text to replace the old_string

    The tool will replace ONE occurrence of old_string with new_string in the specified file.

    CRITICAL REQUIREMENTS FOR USING THIS TOOL:

    1. UNIQUENESS: The old_string MUST uniquely identify the specific instance you want to change. This means:
       - Include AT LEAST 3-5 lines of context BEFORE the change point
       - Include AT LEAST 3-5 lines of context AFTER the change point
       - Include all whitespace, indentation, and surrounding code exactly as it appears in the file

    2. SINGLE INSTANCE: This tool can only change ONE instance at a time. If you need to change multiple instances:
       - Make separate calls to this tool for each instance
       - Each call must uniquely identify its specific instance using extensive context

    3. VERIFICATION: Before using this tool:
       - Check how many instances of the target text exist in the file
       - If multiple instances exist, gather enough context to uniquely identify each one
       - Plan separate tool calls for each instance

    WARNING: If you do not follow these requirements:
       - The tool will fail if old_string matches multiple locations
       - The tool will fail if old_string doesn't match exactly (including whitespace)
       - You may change the wrong instance if you don't include enough context

    When making edits:
       - Ensure the edit results in idiomatic, correct code
       - Do not leave the code in a broken state
       - Always use absolute file paths (starting with /)

    If you want to create a new file, use:
       - A new file path, including dir name if needed
       - An empty old_string
       - The new file's contents as new_string

    Remember: when making multiple file edits in a row to the same file, you should prefer to send all edits in a single message with multiple calls to this tool, rather than multiple messages with a single call each.

    Args:
        ctx: The MCP context
        command: The subcommand to execute (ReadFile, WriteFile, EditFile)
        file_path: The path to the file to operate on
        arg1: First optional argument (varies by command)
        arg2: Second optional argument (varies by command)
    """
    if command == "ReadFile":
        # Handle ReadFile command
        offset = int(arg1) if arg1 and arg1.isdigit() else None
        limit = int(arg2) if arg2 and arg2.isdigit() else None

        # We're stubbing out image handling
        # Just use the updated read_file_content function
        return read_file_content(file_path, offset, limit)

    elif command == "WriteFile":
        # Handle WriteFile command
        content = arg1 or ""
        return write_file_content(file_path, content)

    elif command == "EditFile":
        # Handle EditFile command
        old_string = arg1 or ""
        new_string = arg2 or ""
        return edit_file_content(file_path, old_string, new_string)

    else:
        return f"Unknown command: {command}. Available commands: ReadFile, WriteFile, EditFile"

def run():
    """Run the MCP server."""
    mcp.run()

if __name__ == "__main__":
    run()
