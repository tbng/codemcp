#!/usr/bin/env python3

"""End-to-end tests for InitProject subtool."""

import os
import unittest

from codemcp.testing import MCPEndToEndTestCase


class InitProjectTest(MCPEndToEndTestCase):
    """Test the InitProject subtool functionality."""

    async def test_init_project_basic(self):
        """Test basic InitProject functionality with simple TOML file."""
        # The basic codemcp.toml file is already created in the base test setup
        # We'll test that InitProject can read it correctly

        async with self.create_client_session() as session:
            # Call the InitProject tool
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the result contains expected system prompt elements
            self.assertIn("You are an AI assistant", result_text)

    async def test_init_project_complex_toml(self):
        """Test InitProject with a more complex TOML file that exercises all parsing features."""
        # Create a more complex codemcp.toml file with various data types
        complex_toml_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(complex_toml_path, "w") as f:
            f.write("""# Complex TOML file with various data types
project_prompt = \"\"\"
This is a multiline string
with multiple lines
of text.
\"\"\"

[commands]
format = ["./run_format.sh"]
lint = ["./run_lint.sh"]

[commands.test]
command = ["./run_test.sh"]
doc = "Run tests with optional arguments"
""")

        async with self.create_client_session() as session:
            # Call the InitProject tool
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the result contains expected elements from the complex TOML
            self.assertIn("This is a multiline string", result_text)
            self.assertIn("format", result_text)
            self.assertIn("lint", result_text)
            self.assertIn("Run tests with optional arguments", result_text)

    async def test_init_project_with_binary_characters(self):
        """Test InitProject with TOML containing binary/non-ASCII characters to ensure proper handling."""
        # Create a TOML file with non-ASCII characters and binary data
        binary_toml_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(binary_toml_path, "wb") as f:
            f.write(b"""project_prompt = "Testing binary data handling \xC2\xA9\xE2\x84\xA2\xF0\x9F\x98\x8A"

[commands]
format = ["./run_format.sh"]
""")

        async with self.create_client_session() as session:
            # Call the InitProject tool
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the result contains expected elements, ensuring binary data was handled properly
            self.assertIn("format", result_text)


if __name__ == "__main__":
    unittest.main()
