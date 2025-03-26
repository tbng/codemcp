"""Type stubs for the mcp (Model Context Protocol) package.

This module provides type definitions for the mcp package to help with
type checking when using the MCP SDK.
"""

from typing import (
    Any,
    Dict,
    List,
    Optional,
    Union,
)

# Export ClientSession at the top level

# Export StdioServerParameters at the top level
class StdioServerParameters:
    """Parameters for connecting to an MCP server via stdio."""

    def __init__(
        self,
        command: str,
        args: List[str],
        env: Optional[Dict[str, str]] = None,
        cwd: Optional[str] = None,
    ) -> None:
        """Initialize parameters for connecting to an MCP server.

        Args:
            command: The command to run
            args: Arguments to pass to the command
            env: Environment variables to set
            cwd: Working directory for the command
        """
        ...

# Re-export from client.stdio

# Type for MCP content items
class TextContent:
    """A class representing text content."""

    text: str

    def __init__(self, text: str) -> None:
        """Initialize a new TextContent instance.

        Args:
            text: The text content
        """
        ...

# Type for API call results
class CallToolResult:
    """Result of calling a tool via MCP."""

    isError: bool
    content: Union[str, List[TextContent], Any]
