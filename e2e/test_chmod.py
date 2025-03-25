#!/usr/bin/env python3

"""Tests for the Chmod subtool."""

import os
import stat
import unittest

from codemcp.testing import MCPEndToEndTestCase


class ChmodTest(MCPEndToEndTestCase):
    """Test the Chmod subtool."""

    async def test_chmod_basic_functionality(self):
        """Test basic functionality of the chmod tool."""
        # Create a test script file
        test_file_path = os.path.join(self.temp_dir.name, "test_script.py")
        with open(test_file_path, "w") as f:
            f.write("#!/usr/bin/env python3\nprint('Hello, world!')\n")

        # Initial state - file should not be executable
        mode = os.stat(test_file_path).st_mode
        is_executable = bool(mode & stat.S_IXUSR)
        self.assertFalse(is_executable, "File should not be executable initially")

        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # Make the file executable
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "Chmod",
                    "path": test_file_path,
                    "mode": "a+x",
                    "chat_id": chat_id,
                },
            )

            # Verify success message
            self.assertIn("Made file", result_text)

            # Verify file is now executable
            mode = os.stat(test_file_path).st_mode
            is_executable = bool(mode & stat.S_IXUSR)
            self.assertTrue(is_executable, "File should be executable after chmod a+x")

            # Try making it executable again (should be a no-op)
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "Chmod",
                    "path": test_file_path,
                    "mode": "a+x",
                    "chat_id": chat_id,
                },
            )

            # Verify no-op message
            self.assertIn("already executable", result_text)

            # Remove executable permission
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "Chmod",
                    "path": test_file_path,
                    "mode": "a-x",
                    "chat_id": chat_id,
                },
            )

            # Verify success message
            self.assertIn("Removed executable permission", result_text)

            # Verify file is no longer executable
            mode = os.stat(test_file_path).st_mode
            is_executable = bool(mode & stat.S_IXUSR)
            self.assertFalse(
                is_executable, "File should not be executable after chmod a-x"
            )

            # Try removing executable permission again (should be a no-op)
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "Chmod",
                    "path": test_file_path,
                    "mode": "a-x",
                    "chat_id": chat_id,
                },
            )

            # Verify no-op message
            self.assertIn("already non-executable", result_text)

    async def test_chmod_error_handling(self):
        """Test error handling in the chmod tool."""
        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # Test with non-existent file
            non_existent_file = os.path.join(self.temp_dir.name, "nonexistent.py")
            error_text = await self.call_tool_assert_error(
                session,
                "codemcp",
                {
                    "subtool": "Chmod",
                    "path": non_existent_file,
                    "mode": "a+x",
                    "chat_id": chat_id,
                },
            )
            self.assertIn("not exist", error_text.lower())

            # Test with invalid mode
            test_file = os.path.join(self.temp_dir.name, "test_file.py")
            with open(test_file, "w") as f:
                f.write("# Test file")

            error_text = await self.call_tool_assert_error(
                session,
                "codemcp",
                {
                    "subtool": "Chmod",
                    "path": test_file,
                    "mode": "invalid",
                    "chat_id": chat_id,
                },
            )
            # Check for either error message (from main.py or chmod.py)
            self.assertTrue(
                "unsupported chmod mode" in error_text.lower()
                or "mode must be either 'a+x' or 'a-x'" in error_text.lower(),
                f"Expected an error about invalid mode, but got: {error_text}",
            )


if __name__ == "__main__":
    unittest.main()
