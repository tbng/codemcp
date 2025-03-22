#!/usr/bin/env python3

import functools
import logging
import os
import sys
from contextlib import asynccontextmanager
from typing import AsyncGenerator, Optional, Tuple

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

# Global cache for stdio client
_stdio_client_cache: Optional[Tuple] = None  # Will store (read, write, context_manager)
_client_session_cache: Optional[ClientSession] = None
_cached_server_params: Optional[StdioServerParameters] = None


@asynccontextmanager
async def get_cached_client_session() -> AsyncGenerator[ClientSession, None]:
    """Get a cached ClientSession or create a new one if not available."""
    global _stdio_client_cache, _client_session_cache, _cached_server_params

    # Create server parameters for stdio connection to main.py
    server_params = StdioServerParameters(
        command=sys.executable,  # Use the same Python interpreter
        args=[os.path.join(os.path.dirname(__file__), "__main__.py")],  # Use __main__
        env=os.environ.copy(),  # Pass current environment variables
    )

    # Check if we need to initialize a new connection
    if (
        _stdio_client_cache is None
        or _client_session_cache is None
        or _cached_server_params != server_params
    ):
        # Clean up any existing connection before creating a new one
        if _client_session_cache is not None:
            try:
                await _client_session_cache.aclose()
            except Exception:
                logging.warning("Error closing previous client session", exc_info=True)
            _client_session_cache = None
            _stdio_client_cache = None

        # Create new stdio client and session
        cm = stdio_client(server_params)
        read, write = await cm.__aenter__()
        _stdio_client_cache = (read, write, cm)

        session = ClientSession(read, write)
        await session.__aenter__()
        await session.initialize()
        _client_session_cache = session
        _cached_server_params = server_params

    try:
        # Yield the cached session
        yield _client_session_cache
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
    """Cleanup cached client session and stdio client when shutting down."""
    global _stdio_client_cache, _client_session_cache

    # Clean up client session if it exists
    if _client_session_cache is not None:
        try:
            logging.info("Closing cached client session")
            await _client_session_cache.aclose()
        except Exception:
            logging.warning(
                "Error closing client session during cleanup", exc_info=True
            )
        _client_session_cache = None

    # Clean up stdio client if it exists
    if _stdio_client_cache is not None:
        try:
            logging.info("Closing cached stdio client")
            cm = _stdio_client_cache[2]
            await cm.__aexit__(None, None, None)
        except Exception:
            logging.warning("Error closing stdio client during cleanup", exc_info=True)
        _stdio_client_cache = None


def run():
    """Run the MCP server with hot reload capability."""
    configure_logging()
    logging.info("Starting codemcp with hot reload capability")

    try:
        mcp.run()
    finally:
        # Use asyncio to run the cleanup coroutine
        import asyncio

        asyncio.run(cleanup_client_session())


if __name__ == "__main__":
    run()
