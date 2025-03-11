#!/usr/bin/env python3

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock

from expecttest import TestCase

from codemcp.tools.format import format_code, _get_format_command
from codemcp.tools.code_command import check_for_changes


class TestFormat(TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Setup mocks
        self.setup_mocks()

    def setup_mocks(self):
        """Setup mocks for git and subprocess functions"""
        # Patch is_git_repository in code_command.py
        self.is_git_repo_patch = patch("codemcp.tools.code_command.is_git_repository")
        self.mock_is_git_repo = self.is_git_repo_patch.start()
        self.mock_is_git_repo.return_value = True
        self.addCleanup(self.is_git_repo_patch.stop)

        # Patch commit_changes in code_command.py
        self.commit_changes_patch = patch("codemcp.tools.code_command.commit_changes")
        self.mock_commit_changes = self.commit_changes_patch.start()
        self.mock_commit_changes.return_value = (True, "Commit successful")
        self.addCleanup(self.commit_changes_patch.stop)

        # Patch run_command in code_command.py
        self.run_command_patch = patch("codemcp.tools.code_command.run_command")
        self.mock_run_command = self.run_command_patch.start()

        # Set up a default return value for run_command
        mock_result = MagicMock()
        mock_result.stdout = ""
        mock_result.stderr = ""
        self.mock_run_command.return_value = mock_result

        self.addCleanup(self.run_command_patch.stop)

        # Patch normalize_file_path in code_command.py
        self.normalize_path_patch = patch(
            "codemcp.tools.code_command.normalize_file_path"
        )
        self.mock_normalize_path = self.normalize_path_patch.start()
        self.mock_normalize_path.side_effect = lambda x: x
        self.addCleanup(self.normalize_path_patch.stop)

    def create_config_file(self, format_command=None):
        """Create a test codemcp.toml file with the specified format command"""
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")

        if format_command is None:
            format_command = ["./run_format.sh"]

        config_content = "[commands]\n"
        if format_command:
            command_str = str(format_command).replace("'", '"')
            config_content += f"format = {command_str}\n"

        with open(config_path, "w") as f:
            f.write(config_content)

        return config_path

    def test_get_format_command_success(self):
        """Test retrieving format command from config file"""
        # Create a config file with a format command
        expected_command = ["./run_format.sh"]
        self.create_config_file(expected_command)

        # Call the function and check result
        result = _get_format_command(self.temp_dir.name)
        self.assertEqual(result, expected_command)

    def test_get_format_command_missing(self):
        """Test retrieving format command when it's not in the config"""
        # Create a config file without a format command
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write("[commands]\n")

        # Call the function and check result
        result = _get_format_command(self.temp_dir.name)
        self.assertIsNone(result)

    def test_get_format_command_no_config(self):
        """Test retrieving format command when config file doesn't exist"""
        # Call the function with a directory that doesn't have a config file
        empty_dir = os.path.join(self.temp_dir.name, "empty")
        os.makedirs(empty_dir, exist_ok=True)

        result = _get_format_command(empty_dir)
        self.assertIsNone(result)

    def test_check_for_changes_with_changes(self):
        """Test checking for changes when there are changes"""

        # Set up responses for different git commands
        def run_command_side_effect(*args, **kwargs):
            cmd = args[0]
            mock_result = MagicMock()

            if cmd[0:2] == ["git", "rev-parse"]:
                # Return the repo root
                mock_result.stdout = self.temp_dir.name + "\n"
            elif cmd[0:2] == ["git", "status"]:
                # Return changes in git status
                mock_result.stdout = " M modified_file.py\n?? new_file.py\n"
            else:
                mock_result.stdout = ""

            return mock_result

        self.mock_run_command.side_effect = run_command_side_effect

        result = check_for_changes(self.temp_dir.name)
        self.assertTrue(result)

        # Verify the git status command was called with the repo root from rev-parse
        self.mock_run_command.assert_any_call(
            ["git", "status", "--porcelain"],
            cwd=self.temp_dir.name,
            check=True,
            capture_output=True,
            text=True,
        )

    def test_check_for_changes_no_changes(self):
        """Test checking for changes when there are no changes"""

        # Set up responses for different git commands
        def run_command_side_effect(*args, **kwargs):
            cmd = args[0]
            mock_result = MagicMock()

            if cmd[0:2] == ["git", "rev-parse"]:
                # Return the repo root
                mock_result.stdout = self.temp_dir.name + "\n"
            elif cmd[0:2] == ["git", "status"]:
                # Return empty status (no changes)
                mock_result.stdout = ""
            else:
                mock_result.stdout = ""

            return mock_result

        self.mock_run_command.side_effect = run_command_side_effect

        result = check_for_changes(self.temp_dir.name)
        self.assertFalse(result)

    def test_format_code_success(self):
        """Test successful code formatting"""
        # Create a config file
        self.create_config_file()

        # Set up responses for different commands
        def run_command_side_effect(*args, **kwargs):
            cmd = args[0]
            mock_result = MagicMock()

            if cmd[0:2] == ["git", "rev-parse"]:
                # Return the repo root
                mock_result.stdout = self.temp_dir.name + "\n"
            elif cmd[0:2] == ["git", "status"]:
                # Return empty status (no changes)
                mock_result.stdout = ""
            elif cmd == ["./run_format.sh"]:
                # Format command output
                mock_result.stdout = "Formatting successful"
            else:
                mock_result.stdout = ""

            return mock_result

        self.mock_run_command.side_effect = run_command_side_effect

        result = format_code(self.temp_dir.name)
        self.assertEqual(result, "Code formatting successful:\nFormatting successful")

    def test_format_code_with_changes(self):
        """Test code formatting that makes changes to files"""
        # Create a config file
        self.create_config_file()

        # Set up responses for different commands
        def run_command_side_effect(*args, **kwargs):
            cmd = args[0]
            mock_result = MagicMock()

            if cmd[0:2] == ["git", "rev-parse"]:
                # Return the repo root
                mock_result.stdout = self.temp_dir.name + "\n"
            elif cmd[0:2] == ["git", "status"]:
                # Return changes in git status
                mock_result.stdout = " M modified_file.py\n"
            elif cmd == ["./run_format.sh"]:
                # Format command output
                mock_result.stdout = "Formatting successful"
            else:
                mock_result.stdout = ""

            return mock_result

        self.mock_run_command.side_effect = run_command_side_effect

        result = format_code(self.temp_dir.name)
        self.assertEqual(
            result,
            "Code formatting successful and changes committed:\nFormatting successful",
        )

        # Verify commit_changes was called
        self.mock_commit_changes.assert_called_with(
            self.temp_dir.name, "Auto-commit formatting changes"
        )
        # Verify commit_changes was called
        self.mock_commit_changes.assert_called_with(
            self.temp_dir.name, "Auto-commit formatting changes"
        )

    def test_format_code_no_command(self):
        """Test code formatting when no format command is configured"""
        # Create config without format command
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write("[commands]\n")

        result = format_code(self.temp_dir.name)
        self.assertEqual(result, "Error: No format command configured in codemcp.toml")

    def test_format_code_directory_not_found(self):
        """Test code formatting with nonexistent directory"""
        nonexistent_dir = "/path/does/not/exist"

        # Patch os.path.exists to return False for the nonexistent directory
        with patch("os.path.exists", return_value=False):
            result = format_code(nonexistent_dir)
            self.assertEqual(
                result, f"Error: Directory does not exist: {nonexistent_dir}"
            )

    def test_format_code_command_failure(self):
        """Test code formatting when the format command fails"""
        # Create a config file
        self.create_config_file()

        # Set up responses for git commands, but make format command fail
        from subprocess import CalledProcessError

        error = CalledProcessError(1, ["./run_format.sh"])
        error.stderr = "Command failed: syntax error"

        # Configure command responses
        call_count = 0

        def run_command_side_effect(*args, **kwargs):
            nonlocal call_count
            cmd = args[0]

            # First handle git repo commands
            if cmd[0:2] == ["git", "rev-parse"]:
                mock_result = MagicMock()
                mock_result.stdout = self.temp_dir.name + "\n"
                return mock_result

            # Make the format command fail
            if cmd == ["./run_format.sh"]:
                raise error

            # Default response for other commands
            mock_result = MagicMock()
            mock_result.stdout = ""
            return mock_result

        self.mock_run_command.side_effect = run_command_side_effect

        result = format_code(self.temp_dir.name)
        self.assertIn("Error:", result)
        self.assertIn("Format command failed with exit code 1", result)

    def test_format_code_commit_failure(self):
        """Test code formatting when commit fails after changes"""
        # Create a config file
        self.create_config_file()

        # Set up responses for different commands
        def run_command_side_effect(*args, **kwargs):
            cmd = args[0]
            mock_result = MagicMock()

            if cmd[0:2] == ["git", "rev-parse"]:
                # Return the repo root
                mock_result.stdout = self.temp_dir.name + "\n"
            elif cmd[0:2] == ["git", "status"]:
                # Return changes in git status
                mock_result.stdout = " M modified_file.py\n"
            elif cmd == ["./run_format.sh"]:
                # Format command output
                mock_result.stdout = "Formatting successful"
            else:
                mock_result.stdout = ""

            return mock_result

        self.mock_run_command.side_effect = run_command_side_effect

        # Configure commit to fail
        self.mock_commit_changes.return_value = (False, "Commit failed: merge conflict")

        result = format_code(self.temp_dir.name)
        self.assertIn("Code formatting successful but failed to commit changes", result)
        self.assertIn("Commit error: Commit failed: merge conflict", result)
