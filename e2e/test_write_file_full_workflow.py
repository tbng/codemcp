#!/usr/bin/env python3

"""End-to-end tests for the full workflow involving WriteFile."""

import os
import subprocess
import unittest
import re

from codemcp.testing import MCPEndToEndTestCase


class WriteFileFullWorkflowTest(MCPEndToEndTestCase):
    """Test the full workflow of creating a file with WriteFile and checking the commit format."""

    async def test_write_file_commit_markers(self):
        """Simulate a real-world commit via WriteFile and verify that the markers are correct."""
        # File to create
        test_file_path = os.path.join(self.temp_dir.name, "foo.txt")
        content = "foo"

        async with self.create_client_session() as session:
            # First initialize project to get chat_id
            init_result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "subject_line": "feat: add foo.txt file with simple content",
                    "user_prompt": "Create a foo.txt file with minimal content",
                },
            )
            init_result_text = self.extract_text_from_result(init_result)

            # Extract chat_id from the init result
            chat_id_match = re.search(
                r"chat has been assigned a chat ID: ([^\n]+)", init_result_text
            )
            chat_id = chat_id_match.group(1) if chat_id_match else "test-chat-id"

            # Call the WriteFile tool with chat_id
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "WriteFile",
                    "path": test_file_path,
                    "content": content,
                    "description": "Add foo.txt with content 'foo'",
                    "chat_id": chat_id,
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Check that the operation succeeded
            self.assertIn("Successfully wrote to", result_text)

            # Get the commit message
            commit_message = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                cwd=self.temp_dir.name,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout.decode()

            # For debugging - print the exact commit message we're getting
            print(f"Actual commit message:\n{repr(commit_message)}")

            # Check the format of the commit message
            self.assertIn(
                "```git-revs",
                commit_message,
                "START_MARKER missing from commit message",
            )

            # Split the message by the start marker
            parts = commit_message.split("```git-revs")
            self.assertEqual(len(parts), 2, "START_MARKER should appear exactly once")

            before_marker = parts[0]
            after_marker = parts[1]

            # Check for the end marker
            self.assertIn("```", after_marker, "END_MARKER missing from commit message")

            # Split what's after the start marker into what's inside and outside the block
            inside_outside = after_marker.split("```", 1)
            self.assertEqual(
                len(inside_outside), 2, "END_MARKER should appear at least once"
            )

            inside_markers = inside_outside[0].strip()
            after_end_marker = inside_outside[1].strip()

            # Verify revisions are INSIDE the block
            self.assertIn(
                "HEAD",
                inside_markers,
                f"HEAD should be inside markers, got: {inside_markers}",
            )

            # Base revision isn't included in the first commit, so let's not check for it
            # self.assertIn("(Base revision)", inside_markers,
            #              f"(Base revision) should be inside markers, got: {inside_markers}")

            # Verify NO revisions are OUTSIDE the block
            self.assertNotIn(
                "HEAD",
                before_marker,
                f"HEAD found before START_MARKER: {before_marker}",
            )
            self.assertNotIn(
                "(Base revision)",
                before_marker,
                f"(Base revision) found before START_MARKER: {before_marker}",
            )

            self.assertNotIn(
                "HEAD",
                after_end_marker,
                f"HEAD found after END_MARKER: {after_end_marker}",
            )
            self.assertNotIn(
                "(Base revision)",
                after_end_marker,
                f"(Base revision) found after END_MARKER: {after_end_marker}",
            )

            # Verify only codemcp-id is after the END_MARKER
            self.assertTrue(
                after_end_marker.startswith("codemcp-id:"),
                f"Content after END_MARKER should start with 'codemcp-id:', found: '{after_end_marker}'",
            )


if __name__ == "__main__":
    unittest.main()
