#!/usr/bin/env python3

"""End-to-end tests for InitProject subtool."""

import os
import unittest

from codemcp.testing import MCPEndToEndTestCase


class InitProjectTest(MCPEndToEndTestCase):
    """Test the InitProject subtool functionality."""

    async def test_reuse_head_chat_id(self):
        """Test that reuse_head_chat_id=True reuses the chat ID from the HEAD commit."""
        # Set up a git repository in the temp dir
        import subprocess
        from codemcp.git import get_head_commit_chat_id

        # Create a simple codemcp.toml file
        toml_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(toml_path, "w") as f:
            f.write("""
project_prompt = "Test reuse chat ID"
[commands]
test = ["./run_test.sh"]
""")

        # Set up a git repository
        subprocess.run(["git", "init"], cwd=self.temp_dir.name, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir.name,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir.name,
            check=True,
        )

        # First InitProject call to create a commit with a chat ID
        async with self.create_client_session() as session:
            result1 = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "First initialization",
                    "subject_line": "feat: first commit",
                },
            )

            # Extract the chat ID from the result
            normalized_result1 = self.normalize_path(result1)
            result_text1 = self.extract_text_from_result(normalized_result1)
            import re

            chat_id_match = re.search(r"chat ID: ([\w-]+)", result_text1)
            self.assertIsNotNone(chat_id_match, "Chat ID not found in result")
            original_chat_id = chat_id_match.group(1)

            # Verify the chat ID is also in the commit
            head_chat_id = await get_head_commit_chat_id(self.temp_dir.name)
            self.assertEqual(
                original_chat_id, head_chat_id, "Chat ID not found in HEAD commit"
            )

        # Second InitProject call with reuse_head_chat_id=True
        async with self.create_client_session() as session:
            result2 = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Continue working on the same feature",
                    "subject_line": "feat: continue working",
                    "reuse_head_chat_id": True,
                },
            )

            # Extract the chat ID from the result
            normalized_result2 = self.normalize_path(result2)
            result_text2 = self.extract_text_from_result(normalized_result2)
            chat_id_match = re.search(r"chat ID: ([\w-]+)", result_text2)
            self.assertIsNotNone(chat_id_match, "Chat ID not found in result")
            reused_chat_id = chat_id_match.group(1)

            # Verify the chat ID is the same as the original
            self.assertEqual(original_chat_id, reused_chat_id, "Chat ID not reused")

    async def test_init_project_basic(self):
        """Test basic InitProject functionality with simple TOML file."""
        # The basic codemcp.toml file is already created in the base test setup
        # We'll test that InitProject can read it correctly

        async with self.create_client_session() as session:
            # Call the InitProject tool
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the result contains expected system prompt elements
            self.assertIn("You are an AI assistant", result_text)

    async def test_init_project_complex_toml(self):
        """Test InitProject with a more complex TOML file that exercises all parsing features."""
        # Create a more complex codemcp.toml file with various data types
        complex_toml_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(complex_toml_path, "w") as f:
            f.write("""# Complex TOML file with various data types
project_prompt = \"\"\"
This is a multiline string
with multiple lines
of text.
\"\"\"

[commands]
format = ["./run_format.sh"]
lint = ["./run_lint.sh"]

[commands.test]
command = ["./run_test.sh"]
doc = "Run tests with optional arguments"
""")

        async with self.create_client_session() as session:
            # Call the InitProject tool
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the result contains expected elements from the complex TOML
            self.assertIn("This is a multiline string", result_text)
            self.assertIn("format", result_text)
            self.assertIn("lint", result_text)
            self.assertIn("Run tests with optional arguments", result_text)

    async def test_init_project_with_binary_characters(self):
        """Test InitProject with TOML containing binary/non-ASCII characters to ensure proper handling."""
        # Create a TOML file with non-ASCII characters and binary data
        binary_toml_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(binary_toml_path, "wb") as f:
            f.write(b"""project_prompt = "Testing binary data handling \xc2\xa9\xe2\x84\xa2\xf0\x9f\x98\x8a"

[commands]
format = ["./run_format.sh"]
""")

        async with self.create_client_session() as session:
            # Call the InitProject tool
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                },
            )

            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # Verify the result contains expected elements, ensuring binary data was handled properly
            self.assertIn("format", result_text)

    async def test_allow_empty_commit_flag(self):
        """Test that allow_empty=True flag is properly honored in git.commit_changes."""
        import subprocess
        from codemcp.git import commit_changes

        # Set up a git repository in the temp dir
        subprocess.run(["git", "init"], cwd=self.temp_dir.name, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir.name,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir.name,
            check=True,
        )

        # Make an initial commit so we have a HEAD reference
        test_file = os.path.join(self.temp_dir.name, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("Initial content")

        subprocess.run(["git", "add", "."], cwd=self.temp_dir.name, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"],
            cwd=self.temp_dir.name,
            check=True,
        )

        # Now try to make an empty commit with allow_empty=False (should fail to commit)
        success, message = await commit_changes(
            path=self.temp_dir.name,
            description="This should not commit",
            chat_id="test-chat-id",
            allow_empty=False,
        )

        # Should return success=True but shouldn't actually make a new commit
        self.assertTrue(success)
        self.assertIn("No changes to commit", message)

        # Get the current commit count to verify no new commit was made
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=self.temp_dir.name,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_count_before = int(result.stdout.strip())

        # Now try with allow_empty=True (should succeed in making an empty commit)
        success, message = await commit_changes(
            path=self.temp_dir.name,
            description="Empty commit test",
            chat_id="test-chat-id",
            allow_empty=True,
        )

        # Should return success=True and have made a new commit
        self.assertTrue(success)
        self.assertIn("Changes committed successfully", message)

        # Verify a new commit was actually created
        result = subprocess.run(
            ["git", "rev-list", "--count", "HEAD"],
            cwd=self.temp_dir.name,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_count_after = int(result.stdout.strip())

        # Ensure we have one more commit now
        self.assertEqual(commit_count_before + 1, commit_count_after)

    async def test_chat_id_from_subject_line(self):
        """Test that the chat ID uses the subject line for the human-readable part."""
        # Create a simple codemcp.toml file
        toml_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(toml_path, "w") as f:
            f.write("""
project_prompt = "Test project"
[commands]
test = ["./run_test.sh"]
""")

        # Set up a git repository
        import subprocess

        subprocess.run(["git", "init"], cwd=self.temp_dir.name, check=True)
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir.name,
            check=True,
        )
        subprocess.run(
            ["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir.name,
            check=True,
        )

        async with self.create_client_session() as session:
            # Call InitProject with a conventional commit style subject line
            result = await session.call_tool(
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Test initialize with subject line",
                    "subject_line": "feat: add new feature with spaces!",
                },
            )

            # Verify that the chat ID contains the slugified subject line
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)

            # The chat ID should be something like "1-feat-add-new-feature-with-spaces"
            # Check that it's not using "untitled"
            self.assertNotIn("untitled", result_text)
            # Check that a slugified version of the subject line is in the chat ID
            self.assertIn("feat-add-new-feature-with-spaces", result_text)


if __name__ == "__main__":
    unittest.main()
