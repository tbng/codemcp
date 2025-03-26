"""Type stubs for the mcp.ClientSession class.

This module provides type definitions for the mcp.ClientSession class.
"""

from typing import (
    Any,
    Dict,
    List,
    TypeVar,
    Union,
)

T = TypeVar("T")

class CallToolResult:
    """Result of calling a tool via MCP."""

    isError: bool
    content: Union[str, List["TextContent"], Any]

class TextContent:
    """A class representing text content."""

    text: str

    def __init__(self, text: str) -> None:
        """Initialize a new TextContent instance.

        Args:
            text: The text content
        """
        ...

class ClientSession:
    """A session for interacting with an MCP server."""

    def __init__(self, read: Any, write: Any) -> None:
        """Initialize a new ClientSession.

        Args:
            read: A callable that reads from the server
            write: A callable that writes to the server
        """
        ...

    async def initialize(self) -> None:
        """Initialize the session."""
        ...

    async def call_tool(self, name: str, arguments: Dict[str, Any]) -> CallToolResult:
        """Call a tool on the MCP server.

        Args:
            name: The name of the tool to call
            arguments: Dictionary of arguments to pass to the tool

        Returns:
            An object with isError and content attributes
        """
        ...

    async def __aenter__(self) -> "ClientSession": ...
    async def __aexit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None: ...
