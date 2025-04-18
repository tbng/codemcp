#!/usr/bin/env python3

"""Tests for the Git operations disabled functionality."""

import os
import unittest
from unittest import mock

from codemcp.testing import MCPEndToEndTestCase


class GitOperationsDisabledTest(MCPEndToEndTestCase):
    """Test that Git operations can be disabled via configuration."""

    def setUp(self):
        # Call the parent setUp method
        super().setUp()

        # Set up a patch for the git_operations_enabled function
        self.git_enabled_patch = mock.patch(
            "codemcp.config.git_operations_enabled", return_value=False
        )
        self.git_enabled_patch.start()

    def tearDown(self):
        # Stop the patch
        self.git_enabled_patch.stop()

        # Call the parent tearDown method
        super().tearDown()

    async def asyncSetUp(self):
        """Async setup method with git operations disabled."""
        await super().asyncSetUp()

    async def test_write_file_git_disabled(self):
        """Test that WriteFile works without creating Git commits when Git operations are disabled."""
        # Create a test file path
        test_file_path = os.path.join(self.temp_dir.name, "write_test.txt")
        content = "New content with Git operations disabled"

        # Get the initial git state before the operation
        initial_log = await self.git_run(["log", "--oneline"], capture_output=True, text=True)
        initial_commit_count = len(initial_log.splitlines())

        async with self.create_client_session() as session:
            # First initialize project to get chat_id
            init_result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Test initialization with Git operations disabled",
                    "subject_line": "test: initialize with Git operations disabled",
                    "reuse_head_chat_id": False,
                },
            )

            # Extract chat_id from the init result
            chat_id = self.extract_chat_id_from_text(init_result_text)

            # Call the WriteFile tool with chat_id
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "WriteFile",
                    "path": test_file_path,
                    "content": content,
                    "description": "Create file with Git operations disabled",
                    "chat_id": chat_id,
                },
            )

            # Verify the success message indicates Git operations were disabled
            self.assertIn("Successfully wrote to", result_text)
            self.assertIn("Git operations are disabled", result_text)

            # Verify the file was created with the correct content
            with open(test_file_path) as f:
                file_content = f.read()
            self.assertEqual(file_content, content + "\n")

            # Verify no Git commit was created
            after_log = await self.git_run(["log", "--oneline"], capture_output=True, text=True)
            after_commit_count = len(after_log.splitlines())
            self.assertEqual(
                after_commit_count,
                initial_commit_count,
                "No new commits should be created when Git operations are disabled",
            )

            # Check git status - the file should be untracked
            status = await self.git_run(["status"], capture_output=True, text=True)
            self.assertIn("Untracked files:", status)
            self.assertIn("write_test.txt", status)

    async def test_edit_file_git_disabled(self):
        """Test that EditFile works without creating Git commits when Git operations are disabled."""
        # Create a test file with multiple lines for good context
        test_file_path = os.path.join(self.temp_dir.name, "edit_file.txt")
        original_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
        with open(test_file_path, "w") as f:
            f.write(original_content)

        # Add the file to git and commit it manually
        await self.git_run(["add", "edit_file.txt"])
        await self.git_run(["commit", "-m", "Add file for editing"])

        # Get the initial git state before the operation
        initial_log = await self.git_run(["log", "--oneline"], capture_output=True, text=True)
        initial_commit_count = len(initial_log.splitlines())

        # Edit the file using the EditFile subtool with proper context
        old_string = "Line 1\nLine 2\nLine 3\n"
        new_string = "Line 1\nModified Line 2\nLine 3\n"

        async with self.create_client_session() as session:
            # First initialize project to get chat_id
            init_result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Test initialization for edit with Git operations disabled",
                    "subject_line": "test: initialize for edit with Git operations disabled",
                    "reuse_head_chat_id": False,
                },
            )

            # Extract chat_id from the init result
            chat_id = self.extract_chat_id_from_text(init_result_text)

            # Call the EditFile tool with chat_id
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": test_file_path,
                    "old_string": old_string,
                    "new_string": new_string,
                    "description": "Modify line 2 with Git operations disabled",
                    "chat_id": chat_id,
                },
            )

            # Verify the success message indicates Git operations were disabled
            self.assertIn("Successfully edited", result_text)
            self.assertIn("Git operations are disabled", result_text)

            # Verify the file was edited correctly
            with open(test_file_path) as f:
                file_content = f.read()

            expected_content = "Line 1\nModified Line 2\nLine 3\nLine 4\nLine 5\n"
            self.assertEqual(file_content, expected_content)

            # Verify no Git commit was created
            after_log = await self.git_run(["log", "--oneline"], capture_output=True, text=True)
            after_commit_count = len(after_log.splitlines())
            self.assertEqual(
                after_commit_count,
                initial_commit_count,
                "No new commits should be created when Git operations are disabled",
            )

            # Check git status - the file should be modified but not committed
            status = await self.git_run(["status"], capture_output=True, text=True)
            self.assertIn("modified:", status)
            self.assertIn("edit_file.txt", status)

    async def test_create_reference_with_git_disabled(self):
        """Test that InitProject works without creating Git references when Git operations are disabled."""
        # Get the initial git state before the operation
        initial_log = await self.git_run(["log", "--oneline"], capture_output=True, text=True)
        initial_commit_count = len(initial_log.splitlines())

        # Attempt to list any codemcp refs before initialization
        initial_refs = await self.git_run(
            ["show-ref", "--glob", "refs/codemcp/*"],
            capture_output=True,
            text=True,
            check=False,
        )
        initial_ref_count = len(initial_refs.splitlines()) if initial_refs else 0

        async with self.create_client_session() as session:
            # Initialize project with Git operations disabled
            init_result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Test initialization with Git operations disabled",
                    "subject_line": "test: initialize with Git operations disabled",
                    "reuse_head_chat_id": False,
                },
            )

            # Verify the initialization succeeded despite Git operations being disabled
            self.assertIn("Initialized project", init_result_text)
            self.assertIn("Git operations are disabled", init_result_text)

            # Extract chat_id from the init result
            chat_id = self.extract_chat_id_from_text(init_result_text)

            # Verify chat_id was generated
            self.assertIsNotNone(chat_id, "Chat ID should be generated even with Git operations disabled")

            # Verify no Git commit or reference was created
            after_log = await self.git_run(["log", "--oneline"], capture_output=True, text=True)
            after_commit_count = len(after_log.splitlines())
            self.assertEqual(
                after_commit_count,
                initial_commit_count,
                "No new commits should be created when Git operations are disabled",
            )

            # Verify no new Git reference was created
            after_refs = await self.git_run(
                ["show-ref", "--glob", "refs/codemcp/*"],
                capture_output=True,
                text=True,
                check=False,
            )
            after_ref_count = len(after_refs.splitlines()) if after_refs else 0
            self.assertEqual(
                after_ref_count,
                initial_ref_count,
                "No new Git references should be created when Git operations are disabled",
            )

    async def test_untracked_file_with_git_disabled(self):
        """Test that untracked files can be edited when Git operations are disabled."""
        # Create an untracked file (not added to git)
        untracked_file_path = os.path.join(self.temp_dir.name, "untracked_for_edit.txt")
        with open(untracked_file_path, "w") as f:
            f.write("Initial content in untracked file")

        # Verify the file exists but is not tracked by git
        file_exists = os.path.exists(untracked_file_path)
        self.assertTrue(file_exists, "Test file should exist on filesystem")

        # Check that the file is untracked
        ls_files_output = await self.git_run(
            ["ls-files", untracked_file_path], capture_output=True, text=True
        )
        self.assertEqual(ls_files_output, "", "File should not be tracked by git")

        async with self.create_client_session() as session:
            # First initialize project to get chat_id
            init_result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Test initialization for untracked file with Git disabled",
                    "subject_line": "test: initialize for untracked file with Git disabled",
                    "reuse_head_chat_id": False,
                },
            )

            # Extract chat_id from the init result
            chat_id = self.extract_chat_id_from_text(init_result_text)

            # Try to edit the untracked file - should succeed with Git operations disabled
            new_content = "This content should be written to untracked file"
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": untracked_file_path,
                    "old_string": "Initial content in untracked file",
                    "new_string": new_content,
                    "description": "Edit untracked file with Git operations disabled",
                    "chat_id": chat_id,
                },
            )

            # Verify the edit succeeded
            self.assertIn("Successfully edited", result_text)
            self.assertIn("Git operations are disabled", result_text)

            # Verify the file content was changed
            with open(untracked_file_path) as f:
                actual_content = f.read()
            self.assertEqual(actual_content, new_content + "\n")

            # Verify the file is still untracked
            status = await self.git_run(["status"], capture_output=True, text=True)
            self.assertIn("Untracked files:", status)
            self.assertIn("untracked_for_edit.txt", status)

    async def test_run_command_with_git_disabled(self):
        """Test that running commands works properly when Git operations are disabled."""
        # Create a test script that will modify files
        test_script_path = os.path.join(self.temp_dir.name, "format.sh")
        with open(test_script_path, "w") as f:
            f.write("#!/bin/sh\necho 'Modified by format script' > modified_by_script.txt\n")

        # Make the script executable
        await self.git_run(["update-index", "--chmod=+x", test_script_path])
        os.chmod(test_script_path, 0o755)  # Make executable

        # Add the script to git and commit it
        await self.git_run(["add", test_script_path])
        await self.git_run(["commit", "-m", "Add test format script"])

        # Also create a codemcp.toml file with the format command
        codemcp_toml_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(codemcp_toml_path, "w") as f:
            f.write('[commands]\nformat = ["./format.sh"]\n')

        # Add and commit the toml file
        await self.git_run(["add", codemcp_toml_path])
        await self.git_run(["commit", "-m", "Add codemcp.toml with format command"])

        # Get the initial git state before the operation
        initial_log = await self.git_run(["log", "--oneline"], capture_output=True, text=True)
        initial_commit_count = len(initial_log.splitlines())

        async with self.create_client_session() as session:
            # First initialize project to get chat_id
            init_result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "InitProject",
                    "path": self.temp_dir.name,
                    "user_prompt": "Test initialization for run command with Git disabled",
                    "subject_line": "test: initialize for run command with Git disabled",
                    "reuse_head_chat_id": False,
                },
            )

            # Extract chat_id from the init result
            chat_id = self.extract_chat_id_from_text(init_result_text)

            # Run the format command
            result_text = await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "RunCommand",
                    "path": self.temp_dir.name,
                    "command": "format",
                    "arguments": "",
                    "chat_id": chat_id,
                },
            )

            # Verify the command ran successfully
            self.assertIn("Command executed successfully", result_text)

            # Verify the script created the expected file
            modified_file_path = os.path.join(self.temp_dir.name, "modified_by_script.txt")
            self.assertTrue(
                os.path.exists(modified_file_path),
                "Script should have created a file"
            )

            # Verify file content
            with open(modified_file_path) as f:
                content = f.read()
            self.assertEqual(content, "Modified by format script\n")

            # Verify no Git commit was created despite file changes
            after_log = await self.git_run(["log", "--oneline"], capture_output=True, text=True)
            after_commit_count = len(after_log.splitlines())
            self.assertEqual(
                after_commit_count,
                initial_commit_count,
                "No new commits should be created when Git operations are disabled",
            )

            # Check git status - the new file should be untracked
            status = await self.git_run(["status"], capture_output=True, text=True)
            self.assertIn("Untracked files:", status)
            self.assertIn("modified_by_script.txt", status)


class OutOfProcessGitOperationsDisabledTest(GitOperationsDisabledTest):
    in_process = False


if __name__ == "__main__":
    unittest.main()
