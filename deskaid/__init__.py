#!/usr/bin/env python3

import os
import sys
from typing import Optional, Dict, Any, List, Tuple
import base64
from pathlib import Path
import logging

from mcp.server.fastmcp import FastMCP, Context, Image

from .tools.read_file import read_file_content
from .tools.write_file import write_file_content
from .tools.edit_file import edit_file_content
from .tools.ls import ls_directory

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

    ## LS directory_path

    Lists files and directories in a given path. The path parameter must be an absolute path, not a relative path. You should generally prefer the Glob and Grep tools, if you know which directories to search.

    Args:
        ctx: The MCP context
        command: The subcommand to execute (ReadFile, WriteFile, EditFile, LS)
        file_path: The path to the file or directory to operate on
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

    elif command == "LS":
        # Handle LS command
        return ls_directory(file_path)

    else:
        return f"Unknown command: {command}. Available commands: ReadFile, WriteFile, EditFile, LS"

def configure_logging(log_file='deskaid.log'):
    """Configure logging to write to both a file and the console.

    Debug logging can be enabled by setting the DESKAID_DEBUG environment variable to any value.
    Example: DESKAID_DEBUG=1 python -m deskaid
    """
    log_dir = os.path.join(os.path.expanduser('~'), '.deskaid')
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Determine log level from environment variable
    debug_enabled = os.environ.get('DESKAID_DEBUG') or True
    log_level = logging.DEBUG if debug_enabled else logging.INFO

    # Create a root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Clear any existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # Create file handler
    file_handler = logging.FileHandler(log_path)
    file_handler.setLevel(log_level)

    # Create console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)

    # Create formatter and add it to the handlers
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Add the handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info(f"Logging configured. Log file: {log_path}")
    if debug_enabled:
        logging.debug("Debug logging enabled")

def run():
    """Run the MCP server."""
    configure_logging()
    mcp.run()

if __name__ == "__main__":
    run()
