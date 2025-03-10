#!/usr/bin/env python3

import base64
import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mcp.server.fastmcp import Context, FastMCP, Image

from .tools.edit_file import edit_file_content
from .tools.grep import grep_files
from .tools.init_project import init_project
from .tools.ls import ls_directory
from .tools.read_file import read_file_content
from .tools.write_file import write_file_content

# Initialize FastMCP server
mcp = FastMCP("codemcp")


@mcp.tool()
async def codemcp(
    ctx: Context,
    command: str,
    *,
    file_path: Optional[str] = None,
    content: Optional[str] = None,
    old_string: Optional[str] = None,
    new_string: Optional[str] = None,
    offset: Optional[int] = None,
    limit: Optional[int] = None,
    description: Optional[str] = None,
    pattern: Optional[str] = None,
    path: Optional[str] = None,
    include: Optional[str] = None,
) -> str:
    """
    This is a multipurpose tool that supports the following subcommands:

    ## ReadFile file_path offset? limit?

    Reads a file from the local filesystem. The file_path parameter must be an absolute path, not a relative path. By default, it reads up to ${MAX_LINES_TO_READ} lines starting from the beginning of the file. You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters. Any lines longer than ${MAX_LINE_LENGTH} characters will be truncated. For image files, the tool will display the image for you.

    ## WriteFile file_path content description

    Write a file to the local filesystem. Overwrites the existing file if there is one.
    Provide a short description of the change.

    Before using this tool:

    1. Use the ReadFile tool to understand the file's contents and context

    2. Directory Verification (only applicable when creating new files):
       - Use the LS tool to verify the parent directory exists and is the correct location

    ## EditFile file_path old_string new_string description

    This is a tool for editing files. For larger edits, use the Write tool to overwrite files.
    Provide a short description of the change.

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
    
    ## Grep pattern path include?
    
    Searches for files containing a specified pattern (regular expression) using git grep.
    Files with a match are returned, up to a maximum of 100 files.
    Note that this tool only works inside git repositories.
    
    Example:
      Grep "function.*hello" /path/to/repo  # Find files containing functions with "hello" in their name
      Grep "console\\.log" /path/to/repo --include="*.js"  # Find JS files with console.log statements
    
    ## InitProject directory_path
    
    Initializes a project by reading the .codemcprules TOML file from the specified directory.
    Returns instructions which you should IMMEDIATELY follow before continuing.

    Args:
        ctx: The MCP context
        command: The subcommand to execute (ReadFile, WriteFile, EditFile, LS, InitProject)
        file_path: The path to the file or directory to operate on
        content: Content for WriteFile command
        old_string: String to replace for EditFile command
        new_string: Replacement string for EditFile command
        offset: Line offset for ReadFile command
        limit: Line limit for ReadFile command
        description: Short description of the change (for WriteFile/EditFile)
    """
    # Define expected parameters for each command
    expected_params = {
        "ReadFile": {"file_path", "offset", "limit"},
        "WriteFile": {"file_path", "content", "description"},
        "EditFile": {"file_path", "old_string", "new_string", "description"},
        "LS": {"file_path"},
        "InitProject": {"file_path"},
        "Grep": {"pattern", "path", "include"},
    }

    # Check if command exists
    if command not in expected_params:
        return f"Unknown command: {command}. Available commands: {', '.join(expected_params.keys())}"

    # Get all provided non-None parameters
    provided_params = {
        param: value
        for param, value in {
            "file_path": file_path,
            "content": content,
            "old_string": old_string,
            "new_string": new_string,
            "offset": offset,
            "limit": limit,
            "description": description,
            "pattern": pattern,
            "path": path,
            "include": include,
        }.items()
        if value is not None
    }

    # Check for unexpected parameters
    unexpected_params = set(provided_params.keys()) - expected_params[command]
    if unexpected_params:
        return f"Error: Unexpected parameters for {command} command: {', '.join(unexpected_params)}"

    # Now handle each command with its expected parameters
    if command == "ReadFile":
        if file_path is None:
            return "Error: file_path is required for ReadFile command"

        return read_file_content(file_path, offset, limit)

    elif command == "WriteFile":
        if file_path is None:
            return "Error: file_path is required for WriteFile command"
        if description is None:
            return "Error: description is required for WriteFile command"

        content_str = content or ""
        return write_file_content(file_path, content_str, description)

    elif command == "EditFile":
        if file_path is None:
            return "Error: file_path is required for EditFile command"
        if description is None:
            return "Error: description is required for EditFile command"

        old_str = old_string or ""
        new_str = new_string or ""
        return edit_file_content(file_path, old_str, new_str, None, description)

    elif command == "LS":
        if file_path is None:
            return "Error: file_path is required for LS command"

        return ls_directory(file_path)
        
    elif command == "InitProject":
        if file_path is None:
            return "Error: file_path is required for InitProject command"

        return init_project(file_path)
        
    elif command == "Grep":
        if pattern is None:
            return "Error: pattern is required for Grep command"
        
        if path is None:
            path = file_path
            
        try:
            result = grep_files(pattern, path, include)
            return result.get("resultForAssistant", 
                            f"Found {result.get('numFiles', 0)} file(s)")
        except Exception as e:
            return f"Error executing grep: {str(e)}"


def configure_logging(log_file="codemcp.log"):
    """Configure logging to write to both a file and the console.

    The log level is determined from the configuration file ~/.codemcprc.
    It can be overridden by setting the DESKAID_DEBUG environment variable.
    Example: DESKAID_DEBUG=1 python -m codemcp

    By default, logs from the 'mcp' module are filtered out unless in debug mode.
    """
    from .config import get_logger_verbosity

    log_dir = os.path.join(os.path.expanduser("~"), ".codemcp")
    os.makedirs(log_dir, exist_ok=True)
    log_path = os.path.join(log_dir, log_file)

    # Get log level from config, with environment variable override
    log_level_str = os.environ.get("DESKAID_DEBUG_LEVEL") or get_logger_verbosity()

    # Map string log level to logging constants
    log_level_map = {
        "DEBUG": logging.DEBUG,
        "INFO": logging.INFO,
        "WARNING": logging.WARNING,
        "ERROR": logging.ERROR,
        "CRITICAL": logging.CRITICAL,
    }

    # Convert string to logging level, default to INFO if invalid
    log_level = log_level_map.get(log_level_str.upper(), logging.INFO)

    # Force DEBUG level if DESKAID_DEBUG is set (for backward compatibility)
    debug_mode = False
    if os.environ.get("DESKAID_DEBUG"):
        log_level = logging.DEBUG
        debug_mode = True

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
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)

    # Set up filter to exclude logs from 'mcp' module unless in debug mode
    class ModuleFilter(logging.Filter):
        def filter(self, record):
            # Allow all logs in debug mode, otherwise filter 'mcp' module
            if debug_mode or not record.name.startswith("mcp"):
                return True
            return False

    module_filter = ModuleFilter()
    file_handler.addFilter(module_filter)
    console_handler.addFilter(module_filter)

    # Add the handlers to the root logger
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)

    logging.info(f"Logging configured. Log file: {log_path}")
    logging.info(f"Log level set to: {logging.getLevelName(log_level)}")
    if not debug_mode:
        logging.info("Logs from 'mcp' module are being filtered")


def run():
    """Run the MCP server."""
    configure_logging()
    mcp.run()


if __name__ == "__main__":
    run()
