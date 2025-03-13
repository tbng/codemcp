#!/usr/bin/env python3

"""Tests for git reference markers in commit messages."""

import os
import subprocess
import unittest

from codemcp.git import create_commit_reference
from codemcp.testing import MCPEndToEndTestCase


class GitReferenceMarkersTest(MCPEndToEndTestCase):
    """Test git reference markers in commit messages."""

    async def test_create_commit_reference_markers(self):
        """Test that create_commit_reference properly includes START_MARKER and END_MARKER tokens."""
        # Create a commit reference with a custom message
        chat_id = "test-markers-id"
        description = "Test commit reference with markers"

        # We'll pass in a more complex message with a description
        success, message, commit_hash = await create_commit_reference(
            self.temp_dir.name,
            description=description,
            chat_id=chat_id,
            custom_message=None,  # No custom message, so it will generate one with markers
        )

        self.assertTrue(success, f"Failed to create commit reference: {message}")
        self.assertTrue(commit_hash, "No commit hash returned")

        # Get the commit message from the reference
        reference_name = f"refs/codemcp/{chat_id}"

        # Get full commit message
        commit_message = subprocess.run(
            ["git", "log", "-1", "--pretty=%B", reference_name],
            cwd=self.temp_dir.name,
            env=self.env,
            stdout=subprocess.PIPE,
            check=True,
        ).stdout.decode()

        # Debug output - print the git log output directly
        subprocess.run(
            ["git", "log", "-1", reference_name],
            cwd=self.temp_dir.name,
            env=self.env,
            check=True,
        )

        # Verify the commit message contains the markers
        self.assertIn(
            "```git-revs",
            commit_message,
            "Commit message should contain START_MARKER (```git-revs)",
        )

        # Verify END_MARKER appears after START_MARKER
        self.assertIn(
            "```",
            commit_message.split("```git-revs")[1],
            "Commit message should contain END_MARKER (```) after START_MARKER",
        )


if __name__ == "__main__":
    unittest.main()
