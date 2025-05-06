#!/usr/bin/env python3

"""Test for listing available tools."""

import unittest

from codemcp.testing import MCPEndToEndTestCase


class ListToolsTest(MCPEndToEndTestCase):
    """Test listing available tools."""

    in_process = False

    async def test_list_tools(self):
        """Test listing available tools."""
        async with self.create_client_session() as session:
            result = await session.list_tools()
            # Verify essential tools are available (check for a few common subtools)
            tool_names = [tool.name for tool in result.tools]
            # Check for the presence of common subtools (now as direct tools)
            self.assertIn("read_file", tool_names)
            self.assertIn("write_file", tool_names)
            self.assertIn("edit_file", tool_names)
            # codemcp tool should no longer be present
            self.assertNotIn("codemcp", tool_names)


if __name__ == "__main__":
    unittest.main()
