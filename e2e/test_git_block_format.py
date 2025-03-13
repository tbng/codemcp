#!/usr/bin/env python3

"""Tests for the Git commit block formatting with git-revs markers."""

import os
import subprocess
import unittest
import re

from codemcp.testing import MCPEndToEndTestCase


class GitBlockFormatTest(MCPEndToEndTestCase):
    """Test the Git commit block formatting with git-revs markers."""

    async def test_commit_message_with_blank_lines(self):
        """Test that commit message with blank lines between commits and codemcp-id handles correctly."""
        # Create a file to edit multiple times
        test_file_path = os.path.join(self.temp_dir.name, "block_format_test.txt")
        initial_content = "Initial content for block format test"

        # Create the file
        with open(test_file_path, "w") as f:
            f.write(initial_content)

        # Add it to git
        subprocess.run(
            ["git", "add", test_file_path],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Commit it
        subprocess.run(
            ["git", "commit", "-m", "Add file for block format test"],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Define a chat_id for our test
        chat_id = "block-format-test-123"

        async with self.create_client_session() as session:
            # First edit with our chat_id
            result1 = await session.call_tool(
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": test_file_path,
                    "old_string": "Initial content for block format test",
                    "new_string": "Modified content for block format test",
                    "description": "First edit for block format test",
                    "chat_id": chat_id,
                },
            )

            # Normalize and check the result
            normalized_result1 = self.normalize_path(result1)
            result_text1 = self.extract_text_from_result(normalized_result1)
            self.assertIn("Successfully edited", result_text1)

            # Get the first commit hash
            first_commit_hash = (
                subprocess.check_output(
                    ["git", "rev-parse", "--short", "HEAD"],
                    cwd=self.temp_dir.name,
                    env=self.env,
                )
                .decode()
                .strip()
            )

            # Get the commit message after first edit
            first_commit_msg = (
                subprocess.check_output(
                    ["git", "log", "-1", "--pretty=%B"],
                    cwd=self.temp_dir.name,
                    env=self.env,
                )
                .decode()
                .strip()
            )

            # Create a custom commit message with problematic spacing between commit list and codemcp-id
            # This simulates the issue in the real-world scenario
            custom_message = f"""wip: First edit for block format test

{first_commit_hash}  (Base revision)
HEAD  First edit for block format test

codemcp-id: {chat_id}

ghstack-source-id: 38dbeceb838a511bb525e4f24c8f534f872c3e1e
Pull Request resolved: https://github.com/ezyang/codemcp/pull/20"""

            # Apply the custom commit message to the current HEAD
            subprocess.run(
                ["git", "commit", "--amend", "-m", custom_message],
                cwd=self.temp_dir.name,
                env=self.env,
                check=True,
            )

            # Second edit with the same chat_id
            result2 = await session.call_tool(
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": test_file_path,
                    "old_string": "Modified content for block format test",
                    "new_string": "Twice modified content for block format test",
                    "description": "Second edit for block format test",
                    "chat_id": chat_id,
                },
            )

            # Normalize and check the result
            normalized_result2 = self.normalize_path(result2)
            result_text2 = self.extract_text_from_result(normalized_result2)
            self.assertIn("Successfully edited", result_text2)

            # Get the updated commit message
            updated_commit_msg = (
                subprocess.check_output(
                    ["git", "log", "-1", "--pretty=%B"],
                    cwd=self.temp_dir.name,
                    env=self.env,
                )
                .decode()
                .strip()
            )

            # Check that the git-revs block format is being used
            self.assertIn("```git-revs", updated_commit_msg)
            self.assertIn("```", updated_commit_msg)

            # Check that the commit information is inside the block
            git_revs_pattern = re.compile(r"```git-revs\n(.*?)\n```", re.DOTALL)
            match = git_revs_pattern.search(updated_commit_msg)
            self.assertIsNotNone(match, "git-revs block not found in commit message")

            block_content = match.group(1)
            self.assertIn(
                first_commit_hash,
                block_content,
                "First commit hash not found in git-revs block",
            )
            self.assertIn(
                "HEAD", block_content, "HEAD marker not found in git-revs block"
            )
            self.assertIn(
                "Second edit",
                block_content,
                "New edit description not found in git-revs block",
            )

            # Examine the entire message to check that metadata is preserved
            self.assertIn(
                f"codemcp-id: {chat_id}",
                updated_commit_msg,
                "codemcp-id not found in commit message",
            )
            self.assertIn(
                "ghstack-source-id:",
                updated_commit_msg,
                "ghstack-source-id not preserved in commit message",
            )
            self.assertIn(
                "Pull Request resolved:",
                updated_commit_msg,
                "Pull Request info not preserved in commit message",
            )


if __name__ == "__main__":
    unittest.main()
