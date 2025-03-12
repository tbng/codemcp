#!/usr/bin/env python3

"""Tests for the LS subtool."""

import os
import unittest

from codemcp.testing import MCPEndToEndTestCase


class LSTest(MCPEndToEndTestCase):
    """Test the LS subtool."""

    async def test_ls(self):
        """Test the LS subtool."""
        # Create a test directory structure
        test_dir = os.path.join(self.temp_dir.name, "test_directory")
        os.makedirs(test_dir)

        with open(os.path.join(test_dir, "file1.txt"), "w") as f:
            f.write("Content of file 1")

        with open(os.path.join(test_dir, "file2.txt"), "w") as f:
            f.write("Content of file 2")

        # Create a subdirectory
        sub_dir = os.path.join(test_dir, "subdirectory")
        os.makedirs(sub_dir)

        with open(os.path.join(sub_dir, "subfile.txt"), "w") as f:
            f.write("Content of subfile")

        async with self.create_client_session() as session:
            # First initialize project to get chat_id
            init_result = await session.call_tool(
                "codemcp",
                {"subtool": "InitProject", "path": self.temp_dir.name},
            )
            init_result_text = self.extract_text_from_result(init_result)

            # Extract chat_id from the init result
            import re

            chat_id_match = re.search(
                r"chat has been assigned a unique ID: ([^\n]+)", init_result_text
            )
            chat_id = chat_id_match.group(1) if chat_id_match else "test-chat-id"

            # Call the LS tool with chat_id
            result = await session.call_tool(
                "codemcp",
                {"subtool": "LS", "path": test_dir, "chat_id": chat_id},
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the result includes all files and directories
            self.assertIn("file1.txt", result_text)
            self.assertIn("file2.txt", result_text)
            self.assertIn("subdirectory", result_text)


if __name__ == "__main__":
    unittest.main()
