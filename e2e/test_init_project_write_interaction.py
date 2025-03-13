#!/usr/bin/env python3

"""Tests for the interaction between InitProject and WriteFile subtools."""

import os
import subprocess
import unittest

from codemcp.testing import MCPEndToEndTestCase


class InitProjectWriteInteractionTest(MCPEndToEndTestCase):
    """Test the interaction between InitProject and WriteFile."""

    async def test_markers_in_first_commit(self):
        """Test that the first commit after InitProject properly contains START_MARKER and END_MARKER."""
        # Path to a new file that doesn't exist yet
        new_file_path = os.path.join(self.temp_dir.name, "first_commit_file.txt")

        self.assertFalse(
            os.path.exists(new_file_path),
            "Test file should not exist initially",
        )

        async with self.create_client_session() as session:
            # First initialize project to get chat_id with a subject line and user prompt
            init_result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "subject_line": "feat: add test feature",
                    "user_prompt": "Test user prompt for InitProject",
                },
            )
            init_result_text = self.extract_text_from_result(init_result)

            # Extract chat_id from the init result
            import re

            chat_id_match = re.search(
                r"chat has been assigned a unique ID: ([^\n]+)", init_result_text
            )
            chat_id = chat_id_match.group(1) if chat_id_match else "test-chat-id"

            # Create a new file
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "WriteFile",
                    "path": new_file_path,
                    "content": "This is the first file after InitProject",
                    "description": "Add first file after InitProject",
                    "chat_id": chat_id,
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Check that the operation succeeded
            self.assertIn("Successfully wrote to", result_text)

            # Verify the file was created
            self.assertTrue(
                os.path.exists(new_file_path),
                "File was not created even though operation reported success",
            )

            # Check content
            with open(new_file_path) as f:
                content = f.read()
            self.assertEqual(content, "This is the first file after InitProject")

            # Verify the file was added to git
            ls_files_output = (
                subprocess.run(
                    ["git", "ls-files", new_file_path],
                    cwd=self.temp_dir.name,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                .stdout.decode()
                .strip()
            )

            # The new file should be tracked in git
            self.assertTrue(
                ls_files_output,
                "New file was created but not added to git",
            )

            # Verify the commit message has the correct markers
            commit_message = subprocess.run(
                ["git", "log", "-1", "--pretty=%B"],
                cwd=self.temp_dir.name,
                env=self.env,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=True,
            ).stdout.decode()

            # Debug output - print the git log output directly
            subprocess.run(
                ["git", "log", "-1"],
                cwd=self.temp_dir.name,
                env=self.env,
                check=True,
            )

            # Check that the commit message contains the START_MARKER and END_MARKER tokens
            self.assertIn(
                "```git-revs",
                commit_message,
                "First commit message should contain START_MARKER (```git-revs)",
            )

            # Verify that END_MARKER appears after START_MARKER
            self.assertIn(
                "```",
                commit_message.split("```git-revs")[1],
                "First commit message should contain END_MARKER (```) after START_MARKER",
            )


if __name__ == "__main__":
    unittest.main()
