#!/usr/bin/env python3

"""Tests for the git_run helper method."""

import os
import subprocess
import unittest

from codemcp.testing import MCPEndToEndTestCase


class GitHelperTest(MCPEndToEndTestCase):
    """Test the git_run helper method."""

    async def test_git_add_and_commit(self):
        """Test basic git add and commit operations using the helper."""
        # Create a test file
        test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        with open(test_file_path, "w") as f:
            f.write("Test content")

        # Add the file using git_run helper
        await self.git_run(["add", "test_file.txt"])

        # Commit the file using git_run helper
        await self.git_run(["commit", "-m", "Add test file"])

        # Get the git log using git_run helper
        log_output = await self.git_run(
            ["log", "--oneline"], capture_output=True, text=True
        )

        # Verify commit appears in log
        self.assertIn("Add test file", log_output)

    async def test_git_status(self):
        """Test git status command using the helper."""
        # Create an untracked file
        test_file_path = os.path.join(self.temp_dir.name, "untracked.txt")
        with open(test_file_path, "w") as f:
            f.write("Untracked content")

        # Get git status using git_run helper
        status_output = await self.git_run(
            ["status", "--porcelain"], capture_output=True, text=True
        )

        # Verify untracked file appears in status
        self.assertIn("?? untracked.txt", status_output)

    async def test_git_error_handling(self):
        """Test error handling in git_run helper."""
        # Try to check out a non-existent branch
        with self.assertRaises(subprocess.CalledProcessError):
            await self.git_run(["checkout", "non-existent-branch"])

        # Run the same command but without error checking
        result = await self.git_run(
            ["checkout", "non-existent-branch"], check=False, capture_output=True
        )
        self.assertNotEqual(result.returncode, 0, "Command should have failed")

    async def test_git_commit_count(self):
        """Test getting commit count using the helper."""
        # Create and commit a series of files
        for i in range(3):
            test_file = os.path.join(self.temp_dir.name, f"file{i}.txt")
            with open(test_file, "w") as f:
                f.write(f"Content {i}")

            await self.git_run(["add", f"file{i}.txt"])
            await self.git_run(["commit", "-m", f"Add file {i}"])

        # Get commit count using git_run helper
        log_output = await self.git_run(
            ["log", "--oneline"], capture_output=True, text=True
        )
        # Count lines (+1 for initial setup commit)
        commit_count = len(log_output.split("\n"))

        # Should have 4 commits (3 new ones + initial repo setup)
        self.assertEqual(commit_count, 4, "Should have 4 commits in total")


if __name__ == "__main__":
    unittest.main()
