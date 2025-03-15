#!/usr/bin/env python3

"""Tests for the Grep subtool."""

import os
import unittest

from codemcp.testing import MCPEndToEndTestCase


class GrepTest(MCPEndToEndTestCase):
    """Test the Grep subtool."""

    async def asyncSetUp(self):
        """Set up the test environment with a git repository."""
        await super().asyncSetUp()

        # Create test files with content for grep testing
        self.create_test_files()

        # Add our test files to git
        await self.git_run(["add", "."])
        await self.git_run(["commit", "-m", "Add test files for grep"])

    def create_test_files(self):
        """Create test files with content for grep testing."""
        # Create a file with a specific pattern
        with open(os.path.join(self.temp_dir.name, "file1.js"), "w") as f:
            f.write(
                "function testFunction() {\n  console.log('Test');\n  return true;\n}"
            )

        # Create another file with a different pattern
        with open(os.path.join(self.temp_dir.name, "file2.js"), "w") as f:
            f.write(
                "const anotherFunction = () => {\n  console.error('Error');\n  return false;\n}"
            )

        # Create a Python file with a pattern
        with open(os.path.join(self.temp_dir.name, "script.py"), "w") as f:
            f.write("def test_function():\n    print('Testing')\n    return True\n")

    async def test_grep_directory(self):
        """Test the Grep subtool on a directory."""
        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # Call the Grep tool with directory path
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "Grep",
                    "path": self.temp_dir.name,
                    "pattern": "console",
                    "chat_id": chat_id,
                },
            )

            # Verify results
            self.assertIn("file1.js", result_text)
            self.assertIn("file2.js", result_text)
            self.assertNotIn(
                "script.py", result_text
            )  # Python file doesn't have "console"

    async def test_grep_specific_file(self):
        """Test the Grep subtool with a specific file path."""
        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # Path to a specific file
            file_path = os.path.join(self.temp_dir.name, "file1.js")

            # Call the Grep tool with file path
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "Grep",
                    "path": file_path,
                    "pattern": "console",
                    "chat_id": chat_id,
                },
            )

            # Verify results - should only find the specific file
            self.assertIn("file1.js", result_text)
            self.assertNotIn("file2.js", result_text)  # Shouldn't grep other files
            self.assertIn("Found 1 file", result_text)  # Should find exactly 1 file

    async def test_grep_with_include_filter(self):
        """Test the Grep subtool with an include filter."""
        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # Call the Grep tool with an include filter
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "Grep",
                    "path": self.temp_dir.name,
                    "pattern": "function",
                    "include": "*.py",
                    "chat_id": chat_id,
                },
            )

            # Verify results - should only find Python files
            self.assertIn("script.py", result_text)
            self.assertNotIn("file1.js", result_text)
            self.assertNotIn("file2.js", result_text)


if __name__ == "__main__":
    unittest.main()
