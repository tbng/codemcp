"""Type stubs for the mcp.client.stdio module.

This module provides type definitions for the mcp.client.stdio module.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Protocol,
    TypeVar,
    Union,
    AsyncContextManager,
    Callable,
    Awaitable,
    Tuple,
    AsyncGenerator,
)
import asyncio
from .. import StdioServerParameters

async def stdio_client(
    server_params: StdioServerParameters, **kwargs: Any
) -> AsyncContextManager[Tuple[Any, Any]]:
    """Create a stdio client connected to an MCP server.

    Args:
        server_params: Parameters for connecting to the server

    Returns:
        A context manager that yields (read, write) handles
    """
    ...
