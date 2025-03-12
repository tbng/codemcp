#!/usr/bin/env python3

import logging
import os

from mcp.server.fastmcp import Context, FastMCP

from .tools.edit_file import edit_file_content
from .tools.grep import grep_files
from .tools.init_project import init_project
from .tools.ls import ls_directory
from .tools.read_file import read_file_content
from .tools.run_command import run_command
from .tools.write_file import write_file_content

# Initialize FastMCP server
mcp = FastMCP("codemcp")


# NB: If you edit this, also edit codemcp/tools/init_project.py
@mcp.tool()
async def codemcp(
    ctx: Context,
    subtool: str,
    *,
    path: str | None = None,
    content: str | None = None,
    old_string: str | None = None,
    new_string: str | None = None,
    offset: int | None = None,
    limit: int | None = None,
    description: str | None = None,
    pattern: str | None = None,
    include: str | None = None,
    command: str | None = None,
    arguments: list[str] | str | None = None,
    old_str: str | None = None,  # Added for backward compatibility
    new_str: str | None = None,  # Added for backward compatibility
    chat_id: str | None = None,  # Added for chat identification
    user_prompt: str | None = None,  # Added for InitProject commit message
    subject_line: str | None = None,  # Added for InitProject commit message
    reuse_head_chat_id: bool
    | None = None,  # Whether to reuse the chat ID from the HEAD commit
) -> str:
    """If and only if the user explicitly asks you to initialize codemcp with
    path, you should invoke this tool with arguments `InitProject
    path`.  This will return instructions which you should
    IMMEDIATELY follow before continuing.

    If the user indicates they want to "amend" or "continue working" on a PR,
    you should set reuse_head_chat_id=True to continue using the same chat ID.

    Arguments:
      subtool: The subtool to run (InitProject, ...)
      path: The path to the file or directory to operate on
      chat_id: A unique ID to identify the chat session (provided by InitProject and required for all tools EXCEPT InitProject)
      user_prompt: The user's original prompt verbatim (for InitProject), starting AFTER instructions to initialize codemcp (e.g., you should exclude "Initialize codemcp for PATH")
      subject_line: A short subject line in Git conventional commit format (for InitProject)
      reuse_head_chat_id: If True, reuse the chat ID from the HEAD commit instead of generating a new one (for InitProject)
      ... (there are other arguments which are documented later)
    """
    # Define expected parameters for each subtool
    expected_params = {
        "ReadFile": {"path", "offset", "limit", "chat_id"},
        "WriteFile": {"path", "content", "description", "chat_id"},
        "EditFile": {
            "path",
            "old_string",
            "new_string",
            "description",
            "old_str",
            "new_str",
            "chat_id",
        },
        "LS": {"path", "chat_id"},
        "InitProject": {
            "path",
            "user_prompt",
            "subject_line",
            "reuse_head_chat_id",
        },  # chat_id is not expected for InitProject as it's generated there
        "RunCommand": {"path", "command", "arguments", "chat_id"},
        "Grep": {"pattern", "path", "include", "chat_id"},
    }

    # Check if subtool exists
    if subtool not in expected_params:
        return f"Unknown subtool: {subtool}. Available subtools: {', '.join(expected_params.keys())}"

    # Handle string arguments - convert to a list with one element
    if isinstance(arguments, str):
        arguments = [arguments]

    # Get all provided non-None parameters
    provided_params = {
        param: value
        for param, value in {
            "path": path,
            "content": content,
            "old_string": old_string,
            "new_string": new_string,
            "offset": offset,
            "limit": limit,
            "description": description,
            "pattern": pattern,
            "include": include,
            "command": command,
            "arguments": arguments,
            # Include backward compatibility parameters
            "old_str": old_str,
            "new_str": new_str,
            # Chat ID for session identification
            "chat_id": chat_id,
            # InitProject commit message parameters
            "user_prompt": user_prompt,
            "subject_line": subject_line,
            # Whether to reuse the chat ID from the HEAD commit
            "reuse_head_chat_id": reuse_head_chat_id,
        }.items()
        if value is not None
    }

    # Check for unexpected parameters
    unexpected_params = set(provided_params.keys()) - expected_params[subtool]
    if unexpected_params:
        return f"Error: Unexpected parameters for {subtool} subtool: {', '.join(unexpected_params)}"

    # Check for required chat_id for all tools except InitProject
    if subtool != "InitProject" and chat_id is None:
        return f"Error: chat_id is required for {subtool} subtool"

    # Now handle each subtool with its expected parameters
    if subtool == "ReadFile":
        if path is None:
            return "Error: path is required for ReadFile subtool"

        return await read_file_content(path, offset, limit, chat_id)

    if subtool == "WriteFile":
        if path is None:
            return "Error: path is required for WriteFile subtool"
        if description is None:
            return "Error: description is required for WriteFile subtool"

        content_str = content or ""
        return await write_file_content(path, content_str, description, chat_id)

    if subtool == "EditFile":
        if path is None:
            return "Error: path is required for EditFile subtool"
        if description is None:
            return "Error: description is required for EditFile subtool"
        if old_string is None and old_str is None:
            # TODO: I want telemetry to tell me when this occurs.
            return "Error: Either old_string or old_str is required for EditFile subtool (use empty string for new file creation)"

        # Accept either old_string or old_str (prefer old_string if both are provided)
        old_content = old_string or old_str or ""
        # Accept either new_string or new_str (prefer new_string if both are provided)
        new_content = new_string or new_str or ""
        return await edit_file_content(
            path, old_content, new_content, None, description, chat_id
        )

    if subtool == "LS":
        if path is None:
            return "Error: path is required for LS subtool"

        return await ls_directory(path, chat_id)

    if subtool == "InitProject":
        if path is None:
            return "Error: path is required for InitProject subtool"

        return await init_project(path, user_prompt, subject_line, reuse_head_chat_id)

    if subtool == "RunCommand":
        # When is something a command as opposed to a subtool?  They are
        # basically the same thing, but commands are always USER defined.
        # This means we shove them all in RunCommand so they are guaranteed
        # not to conflict with codemcp's subtools.

        if path is None:
            return "Error: path is required for RunCommand subtool"
        if command is None:
            return "Error: command is required for RunCommand subtool"

        return await run_command(path, command, arguments, chat_id)

    if subtool == "Grep":
        if pattern is None:
            return "Error: pattern is required for Grep subtool"

        if path is None:
            return "Error: path is required for Grep subtool"

        try:
            result = await grep_files(pattern, path, include, chat_id)
            return result.get(
                "resultForAssistant",
                f"Found {result.get('numFiles', 0)} file(s)",
            )
        except Exception as e:
            logging.warning(
                f"Exception suppressed in grep subtool: {e!s}", exc_info=True
            )
            return f"Error executing grep: {e!s}"


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
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
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
