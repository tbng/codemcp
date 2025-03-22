#!/usr/bin/env python3

import logging
import os
import sys
from typing import List, Union

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server with the same name
mcp = FastMCP("codemcp")


@mcp.tool()
async def codemcp(
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
    arguments: Union[List[str], str, None] = None,
    old_str: str | None = None,  # Added for backward compatibility
    new_str: str | None = None,  # Added for backward compatibility
    chat_id: str | None = None,  # Added for chat identification
    user_prompt: str | None = None,  # Added for InitProject commit message
    subject_line: str | None = None,  # Added for InitProject commit message
    reuse_head_chat_id: bool
    | None = None,  # Whether to reuse the chat ID from the HEAD commit
) -> str:
    """This is a wrapper that forwards all tool calls to the codemcp/main.py process.
    This allows for hot-reloading as main.py will be reloaded on each call.

    Arguments are the same as in main.py's codemcp tool.
    """
    try:
        # Create a subprocess running codemcp/main.py
        module_dir = os.path.dirname(os.path.abspath(__file__))
        main_script = os.path.join(module_dir, "main.py")

        # Create server parameters for stdio connection to main.py
        server_params = StdioServerParameters(
            command=sys.executable,  # Use the same Python interpreter
            args=[main_script],  # Run main.py as the subprocess
            env=os.environ.copy(),  # Pass current environment variables
        )

        # Normalize string arguments - convert to a list with one element
        if isinstance(arguments, str):
            arguments = [arguments]

        # Forward the tool call to the main.py subprocess
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()

                # List available tools to ensure connection is working
                # This also helps validate the subprocess started correctly
                tools = await session.list_tools()
                if not any(tool.name == "codemcp" for tool in tools):
                    raise ValueError(
                        "The codemcp tool is not available in the subprocess"
                    )

                # Call the same tool in the subprocess with all parameters
                tool_args = {}
                # Add all non-None parameters
                for param_name, param_value in {
                    "subtool": subtool,
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
                    "old_str": old_str,
                    "new_str": new_str,
                    "chat_id": chat_id,
                    "user_prompt": user_prompt,
                    "subject_line": subject_line,
                    "reuse_head_chat_id": reuse_head_chat_id,
                }.items():
                    if param_value is not None:
                        tool_args[param_name] = param_value

                # Call the codemcp tool in the subprocess
                result = await session.call_tool("codemcp", arguments=tool_args)

                # Return the result from the subprocess
                return result

    except Exception as e:
        logging.error("Exception in hot_reload_entry.py", exc_info=True)
        return f"Error in hot_reload_entry.py: {str(e)}"


def configure_logging():
    """Import and use the same logging configuration from main module"""
    from .main import configure_logging as main_configure_logging

    main_configure_logging("codemcp_hot_reload.log")


def run():
    """Run the MCP server with hot reload capability."""
    configure_logging()
    logging.info("Starting codemcp with hot reload capability")
    mcp.run()


if __name__ == "__main__":
    run()
