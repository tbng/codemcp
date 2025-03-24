#!/usr/bin/env python3

"""End-to-end tests for the rm tool."""

import os
import unittest

from codemcp.testing import MCPEndToEndTestCase


class RMTest(MCPEndToEndTestCase):
    """Test the RM subtool functionality."""

    async def test_rm_file(self):
        """Test removing a file using the RM subtool."""
        # Create a test file
        test_file_path = os.path.join(self.temp_dir.name, "file_to_remove.txt")
        with open(test_file_path, "w") as f:
            f.write("This file will be removed")

        # Add the file using git
        await self.git_run(["add", "file_to_remove.txt"])
        await self.git_run(["commit", "-m", "Add file that will be removed"])

        # Initial count of commits
        initial_log = await self.git_run(
            ["log", "--oneline"], capture_output=True, text=True
        )
        initial_commit_count = len(initial_log.strip().split("\n"))

        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # For debugging, print some path information
            print(f"DEBUG - Test file path: {test_file_path}")
            # Check if file exists
            print(f"DEBUG - File exists before RM: {os.path.exists(test_file_path)}")

            # Call the RM tool with the chat_id - use absolute path
            result = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "RM",
                    "path": test_file_path,  # Use absolute path
                    "description": "Test file removal",
                    "chat_id": chat_id,
                },
            )

            # Print the result for debugging
            print(f"DEBUG - RM result: {result}")

            # Check that the file no longer exists
            print(f"DEBUG - File exists after RM: {os.path.exists(test_file_path)}")
            self.assertFalse(
                os.path.exists(test_file_path), "File should have been removed"
            )

            # Verify the output message indicates success
            self.assertIn("Successfully removed file", result)

            # Verify a commit was created for the removal
            final_log = await self.git_run(
                ["log", "--oneline"], capture_output=True, text=True
            )
            final_commit_count = len(final_log.strip().split("\n"))
            self.assertEqual(
                final_commit_count,
                initial_commit_count + 1,
                "Should have one more commit",
            )

            # Verify the commit message contains the description
            latest_commit_msg = await self.git_run(
                ["log", "-1", "--pretty=%B"], capture_output=True, text=True
            )
            self.assertIn("Remove file_to_remove.txt", latest_commit_msg)
            self.assertIn("Test file removal", latest_commit_msg)

    async def test_rm_file_does_not_exist(self):
        """Test attempting to remove a non-existent file."""
        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # Attempt to remove a file that doesn't exist - should fail
            result = await self.call_tool_assert_error(
                session,
                "codemcp",
                {
                    "subtool": "RM",
                    "path": "non_existent_file.txt",
                    "description": "Remove non-existent file",
                    "chat_id": chat_id,
                },
            )

            # Verify the operation failed with proper error message
            self.assertIn("File does not exist", result)

    async def test_rm_outside_repo(self):
        """Test attempting to remove a file outside the repository."""
        # Create a file outside the repository
        outside_dir = os.path.join(os.path.dirname(self.temp_dir.name), "outside_repo")
        os.makedirs(outside_dir, exist_ok=True)
        outside_file = os.path.join(outside_dir, "outside_file.txt")
        with open(outside_file, "w") as f:
            f.write("This file is outside the repository")

        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # Attempt to remove the file (using absolute path) - should fail
            result = await self.call_tool_assert_error(
                session,
                "codemcp",
                {
                    "subtool": "RM",
                    "path": outside_file,
                    "description": "Remove file outside repo",
                    "chat_id": chat_id,
                },
            )

            # Verify the operation failed with proper error message
            # Could be either form of the git error message
            self.assertTrue(
                "fatal: not a git repository" in result
                or "not a git repository" in result,
                f"Expected git repository error not found in: {result}",
            )

            # Ensure the file still exists
            self.assertTrue(
                os.path.exists(outside_file), "Outside file should still exist"
            )


if __name__ == "__main__":
    unittest.main()
