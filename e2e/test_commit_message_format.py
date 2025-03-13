#!/usr/bin/env python3

"""Tests for specific commit message formats."""

import os
import subprocess
import unittest
import re

from codemcp.git import create_commit_reference
from codemcp.git_message import update_commit_message_with_description
from codemcp.testing import MCPEndToEndTestCase


class CommitMessageFormatTest(MCPEndToEndTestCase):
    """Test to ensure commit messages have proper format with markers."""

    async def test_end_to_end_commit_format(self):
        """Test the complete flow of creating a file and verifying the resulting commit message format."""
        # Create a new file
        test_file_path = os.path.join(self.temp_dir.name, "foo.txt")
        content = "foo"

        # First create the file
        with open(test_file_path, "w") as f:
            f.write(content)

        # Add the file to git
        subprocess.run(
            ["git", "add", test_file_path],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Create a commit with a custom message that mimics the example with the bug
        subject_line = "feat: add foo.txt file with simple content"
        description = "Add foo.txt with content 'foo'"
        commit_message = f"{subject_line}\n\nAdd a file foo.txt with contents foo"
        chat_id = "test-format-id"

        # Create the commit
        subprocess.run(
            ["git", "commit", "-m", commit_message],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Get the commit hash
        commit_hash = (
            subprocess.run(
                ["git", "rev-parse", "HEAD"],
                cwd=self.temp_dir.name,
                env=self.env,
                stdout=subprocess.PIPE,
                check=True,
            )
            .stdout.decode()
            .strip()
        )

        # Use our function to update the commit message
        updated_message = update_commit_message_with_description(
            current_commit_message=commit_message,
            description=description,
            commit_hash=commit_hash,
            chat_id=chat_id,
        )

        # Print the updated message for debugging
        print(f"Updated message:\n{updated_message}")

        # Check that the message has the expected format
        # 1. Verify start and end markers exist
        self.assertIn("```git-revs", updated_message)

        # Split by start marker
        parts = updated_message.split("```git-revs")
        self.assertEqual(len(parts), 2, "Should only have one ```git-revs marker")

        # Get what's after start marker
        after_start = parts[1]

        # Find end marker position
        end_pos = after_start.find("```")
        self.assertGreater(end_pos, 0, "End marker not found after start marker")

        # Extract content between markers
        between_markers = after_start[:end_pos].strip()

        # Verify that HEAD and Base revision are INSIDE the markers
        self.assertIn("HEAD", between_markers)
        self.assertIn(f"{commit_hash[:7]}", between_markers)
        self.assertIn("(Base revision)", between_markers)

        # Verify nothing is after the end marker except the codemcp-id
        after_end = after_start[end_pos + 3 :].strip()
        self.assertTrue(
            re.match(r"^codemcp-id: [a-zA-Z0-9-]+$", after_end) is not None,
            f"Unexpected content after end marker: '{after_end}'",
        )

        # Specific check for the bug: ensure no revision info is outside the markers
        self.assertNotIn("HEAD", parts[0], "HEAD found before markers")
        self.assertNotIn(
            "(Base revision)", parts[0], "Base revision found before markers"
        )
        self.assertNotIn("HEAD", after_end, "HEAD found after markers")
        self.assertNotIn(
            "(Base revision)", after_end, "Base revision found after markers"
        )

    async def test_direct_update_function(self):
        """Test directly calling update_commit_message_with_description with the example scenario."""
        # Create a message similar to the problematic one
        commit_message = "feat: add foo.txt file with simple content\n\nAdd a file foo.txt with contents foo"
        description = "Add foo.txt with content 'foo'"
        commit_hash = "636c296"  # Mock hash
        chat_id = "82-feat-add-foo-txt-file-with-simple-content"

        # Call the function directly
        updated_message = update_commit_message_with_description(
            current_commit_message=commit_message,
            description=description,
            commit_hash=commit_hash,
            chat_id=chat_id,
        )

        # Also test the buggy format explicitly to catch it:
        buggy_message = f"""feat: add foo.txt file with simple content

Add a file foo.txt with contents foo

```git-revs

```

636c296  (Base revision)
HEAD     Add foo.txt with content 'foo'

codemcp-id: 82-feat-add-foo-txt-file-with-simple-content"""

        print(f"Buggy message to check:\n{buggy_message}")

        # Check if the function output matches the expected format not the buggy one
        self.assertNotEqual(
            updated_message,
            buggy_message,
            "The update function is producing the buggy message format",
        )

        # Print the message for debugging
        print(f"Direct update message:\n{updated_message}")

        # Check that the message has the expected format
        # 1. Verify start and end markers exist
        self.assertIn("```git-revs", updated_message)

        # Split by start marker
        parts = updated_message.split("```git-revs")
        self.assertEqual(len(parts), 2, "Should only have one ```git-revs marker")

        # Get what's after start marker
        after_start = parts[1]

        # Find end marker position
        end_pos = after_start.find("```")
        self.assertGreater(end_pos, 0, "End marker not found after start marker")

        # Extract content between markers
        between_markers = after_start[:end_pos].strip()

        # Verify that HEAD and Base revision are INSIDE the markers
        self.assertIn("HEAD", between_markers)
        self.assertIn(f"{commit_hash}", between_markers)
        self.assertIn("(Base revision)", between_markers)

        # Verify nothing is after the end marker except the codemcp-id
        after_end = after_start[end_pos + 3 :].strip()
        self.assertTrue(
            re.match(r"^codemcp-id: [a-zA-Z0-9-]+$", after_end) is not None,
            f"Unexpected content after end marker: '{after_end}'",
        )


if __name__ == "__main__":
    unittest.main()
