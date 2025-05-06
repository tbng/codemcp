#!/usr/bin/env python3

from mcp.server.fastmcp import FastMCP

# Initialize FastMCP server
mcp = FastMCP("codemcp")

__all__ = [
    "mcp",
]
