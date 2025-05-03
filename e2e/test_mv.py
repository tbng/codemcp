#!/usr/bin/env python3

"""End-to-end tests for the mv tool."""

import os
import unittest

from codemcp.testing import MCPEndToEndTestCase


class MVTest(MCPEndToEndTestCase):
    """Test the MV subtool functionality."""

    async def test_mv_file(self):
        """Test moving a file using the MV subtool."""
        # Create a test file
        source_file_path = os.path.join(self.temp_dir.name, "file_to_move.txt")
        with open(source_file_path, "w") as f:
            f.write("This file will be moved")

        # Create target directory
        target_dir = os.path.join(self.temp_dir.name, "target_dir")
        os.makedirs(target_dir, exist_ok=True)
        target_file_path = os.path.join(target_dir, "moved_file.txt")

        # Add the file using git
        await self.git_run(["add", "file_to_move.txt"])
        await self.git_run(["commit", "-m", "Add file that will be moved"])

        # Initial count of commits
        initial_log = await self.git_run(
            ["log", "--oneline"], capture_output=True, text=True
        )
        initial_commit_count = len(initial_log.strip().split("\n"))

        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # For debugging, print some path information
            print(f"DEBUG - Source file path: {source_file_path}")
            print(f"DEBUG - Target file path: {target_file_path}")
            # Check if files exist
            print(
                f"DEBUG - Source file exists before MV: {os.path.exists(source_file_path)}"
            )
            print(
                f"DEBUG - Target file exists before MV: {os.path.exists(target_file_path)}"
            )

            # Call the MV tool with the chat_id - use absolute paths
            result = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "MV",
                    "source_path": source_file_path,
                    "target_path": target_file_path,
                    "description": "Test file movement",
                    "chat_id": chat_id,
                },
            )

            # Print the result for debugging
            print(f"DEBUG - MV result: {result}")

            # Check that the source file no longer exists
            print(
                f"DEBUG - Source file exists after MV: {os.path.exists(source_file_path)}"
            )
            self.assertFalse(
                os.path.exists(source_file_path), "Source file should have been moved"
            )

            # Check that the target file now exists
            print(
                f"DEBUG - Target file exists after MV: {os.path.exists(target_file_path)}"
            )
            self.assertTrue(
                os.path.exists(target_file_path), "Target file should now exist"
            )

            # Verify the target file has the same content
            with open(target_file_path, "r") as f:
                content = f.read()
            self.assertEqual(content, "This file will be moved")

            # Verify the output message indicates success
            self.assertIn("Successfully moved file", result)

            # Verify a commit was created for the movement
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
            self.assertIn(
                "Move file_to_move.txt -> target_dir/moved_file.txt", latest_commit_msg
            )
            self.assertIn("Test file movement", latest_commit_msg)

    async def test_mv_file_source_does_not_exist(self):
        """Test attempting to move a non-existent source file."""
        # Create target directory
        target_dir = os.path.join(self.temp_dir.name, "target_dir")
        os.makedirs(target_dir, exist_ok=True)
        target_file_path = os.path.join(target_dir, "moved_file.txt")

        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # Attempt to move a file that doesn't exist - should fail
            result = await self.call_tool_assert_error(
                session,
                "codemcp",
                {
                    "subtool": "MV",
                    "source_path": "non_existent_file.txt",
                    "target_path": target_file_path,
                    "description": "Move non-existent file",
                    "chat_id": chat_id,
                },
            )

            # Verify the operation failed with proper error message
            self.assertIn("Source file does not exist", result)

    async def test_mv_outside_repo(self):
        """Test attempting to move a file outside the repository."""
        # Create a file inside the repository
        source_file_path = os.path.join(self.temp_dir.name, "inside_repo_file.txt")
        with open(source_file_path, "w") as f:
            f.write("This file is inside the repository")

        # Add the file using git
        await self.git_run(["add", "inside_repo_file.txt"])
        await self.git_run(["commit", "-m", "Add file inside repo"])

        # Create a directory outside the repository
        outside_dir = os.path.join(os.path.dirname(self.temp_dir.name), "outside_repo")
        os.makedirs(outside_dir, exist_ok=True)
        outside_file = os.path.join(outside_dir, "outside_file.txt")

        async with self.create_client_session() as session:
            # Get a valid chat_id
            chat_id = await self.get_chat_id(session)

            # Attempt to move the file to a location outside the repo - should fail
            result = await self.call_tool_assert_error(
                session,
                "codemcp",
                {
                    "subtool": "MV",
                    "source_path": source_file_path,
                    "target_path": outside_file,
                    "description": "Move file outside repo",
                    "chat_id": chat_id,
                },
            )

            # Verify the operation failed with proper error message
            self.assertIn("not within the git repository", result)

            # Ensure the source file still exists
            self.assertTrue(
                os.path.exists(source_file_path), "Source file should still exist"
            )


if __name__ == "__main__":
    unittest.main()
