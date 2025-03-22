#!/usr/bin/env python3

import asyncio
import functools
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.fastmcp import FastMCP

# Import the original codemcp function from main to clone its signature
from codemcp.main import (
    codemcp as original_codemcp,
)
from codemcp.main import (
    configure_logging as main_configure_logging,
)

# Initialize FastMCP server with the same name
mcp = FastMCP("codemcp")

# Global cache for composed context manager
_client_cm = None
_cached_server_params: Optional[StdioServerParameters] = None


class ComposedStdioClientSession:
    """A class that composes stdio_client and ClientSession context managers."""

    def __init__(self, server_params: StdioServerParameters):
        self.server_params = server_params
        self.stdio_cm = None
        self.session = None
        self.read = None
        self.write = None

    async def __aenter__(self):
        # Enter the stdio_client context manager
        self.stdio_cm = stdio_client(self.server_params)
        self.read, self.write = await self.stdio_cm.__aenter__()

        # Enter the ClientSession context manager
        self.session = ClientSession(self.read, self.write)
        await self.session.__aenter__()

        # Initialize the session
        await self.session.initialize()

        return self.session

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Exit the context managers in reverse order
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
            self.session = None

        if self.stdio_cm:
            await self.stdio_cm.__aexit__(exc_type, exc_val, exc_tb)
            self.stdio_cm = None


@asynccontextmanager
async def get_cached_client_session() -> AsyncGenerator[ClientSession, None]:
    """Get a cached ClientSession or create a new one if not available."""
    global _client_cm, _cached_server_params

    # Create server parameters for stdio connection to main.py
    server_params = StdioServerParameters(
        command=sys.executable,  # Use the same Python interpreter
        args=[os.path.join(os.path.dirname(__file__), "__main__.py")],  # Use __main__
        env=os.environ.copy(),  # Pass current environment variables
    )

    # Check if we need to initialize a new connection
    if _client_cm is None or _cached_server_params != server_params:
        # Clean up any existing connection before creating a new one
        if _client_cm is not None:
            try:
                logging.info("Closing previous client session")
                await _client_cm.__aexit__(None, None, None)
            except Exception:
                logging.warning("Error closing previous client session", exc_info=True)
            _client_cm = None

        # Create new composed context manager
        logging.info("Creating new client session")
        _client_cm = ComposedStdioClientSession(server_params)
        _cached_server_params = server_params

    # Use the cached context manager
    session = await _client_cm.__aenter__()

    try:
        # Yield the session from the context manager
        yield session
    except Exception:
        # Log the exception but don't close the connection on errors
        logging.error("Error using cached client session", exc_info=True)
        raise


@mcp.tool()
@functools.wraps(original_codemcp)  # This copies the signature and docstring
async def codemcp(**kwargs) -> str:
    """This is a wrapper that forwards all tool calls to the codemcp/main.py process.
    This allows for hot-reloading as main.py will be reloaded on each call.

    Arguments are the same as in main.py's codemcp tool.
    """
    configure_logging()
    try:
        async with get_cached_client_session() as session:
            # Call the codemcp tool in the subprocess
            result = await session.call_tool("codemcp", arguments=kwargs)

            # Return the result from the subprocess
            # TODO: This loses the isError-ness
            return result.content

    except Exception as e:
        logging.error("Exception in hot_reload_entry.py", exc_info=True)
        return f"Error in hot_reload_entry.py: {str(e)}"


def configure_logging():
    """Import and use the same logging configuration from main module"""
    main_configure_logging("codemcp_hot_reload.log")


async def cleanup_client_session():
    """Cleanup cached client session when shutting down."""
    global _client_cm

    # Clean up composed context manager if it exists
    if _client_cm is not None:
        try:
            logging.info("Closing cached client session")
            await _client_cm.__aexit__(None, None, None)
        except Exception:
            logging.warning("Error during client session cleanup", exc_info=True)
        _client_cm = None


def run():
    """Run the MCP server with hot reload capability."""
    configure_logging()
    logging.info("Starting codemcp with hot reload capability")

    try:
        mcp.run()
    finally:
        # Use asyncio to run the cleanup coroutine
        asyncio.run(cleanup_client_session())


if __name__ == "__main__":
    run()
