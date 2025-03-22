#!/usr/bin/env python3

import functools
import logging
import os
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP

# Import the original codemcp function from main to clone its signature
from .main import codemcp as original_codemcp

# Initialize FastMCP server with the same name
mcp = FastMCP("codemcp")


@mcp.tool()
@functools.wraps(original_codemcp)  # This copies the signature and docstring
async def codemcp(**kwargs) -> str:
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

        # Normalize string arguments if present - convert to a list with one element
        if "arguments" in kwargs and isinstance(kwargs["arguments"], str):
            kwargs["arguments"] = [kwargs["arguments"]]

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

                # Create a dictionary of non-None parameters to pass to the subprocess
                tool_args = {k: v for k, v in kwargs.items() if v is not None}

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
