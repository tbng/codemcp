#!/usr/bin/env python3

import os
import tempfile
import unittest
import subprocess
from unittest.mock import patch, MagicMock, call

import tomli_w

from codemcp.tools.format import format_code, _get_format_command, _check_for_changes
from codemcp.shell import run_command


class TestFormatTool(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = self.temp_dir.name

    def tearDown(self):
        # Clean up temporary directory
        self.temp_dir.cleanup()

    def test_get_format_command_no_config(self):
        """Test that _get_format_command returns None when no config file exists."""
        result = _get_format_command(self.project_dir)
        self.assertIsNone(result)

    def test_get_format_command_no_format_section(self):
        """Test that _get_format_command returns None when config exists but has no format command."""
        # Create a config file without format command
        config = {"global_prompt": "Test prompt"}
        config_path = os.path.join(self.project_dir, "codemcp.toml")
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        result = _get_format_command(self.project_dir)
        self.assertIsNone(result)

    def test_get_format_command_with_format(self):
        """Test that _get_format_command returns the format command when properly configured."""
        # Create a config file with format command
        format_command = ["./run_format.sh"]
        config = {"commands": {"format": format_command}}
        config_path = os.path.join(self.project_dir, "codemcp.toml")
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        result = _get_format_command(self.project_dir)
        self.assertEqual(result, format_command)

    @patch("codemcp.tools.format.is_git_repository")
    @patch("codemcp.tools.format._check_for_changes")
    @patch("codemcp.tools.format.run_command")
    def test_format_code_success(self, mock_run, mock_check_changes, mock_is_git_repo):
        """Test successful execution of format_code."""
        # Mock git repository check (not a git repo to simplify test)
        mock_is_git_repo.return_value = False

        # Mock successful subprocess run
        mock_process = MagicMock()
        mock_process.stdout = "Formatting successful"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Create a config file with format command
        format_command = ["./run_format.sh"]
        config = {"commands": {"format": format_command}}
        config_path = os.path.join(self.project_dir, "codemcp.toml")
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        result = format_code(self.project_dir)
        self.assertIn("Code formatting successful", result)

        # Check that run_command was called correctly for the format command
        mock_run.assert_called_once_with(
            format_command,
            cwd=self.project_dir,
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("codemcp.tools.format.is_git_repository")
    @patch("codemcp.tools.format.run_command")
    def test_format_code_failure(self, mock_run, mock_is_git_repo):
        """Test format_code when the command fails."""
        # Mock git repository check
        mock_is_git_repo.return_value = False

        # Mock failed subprocess run
        mock_run.side_effect = subprocess.CalledProcessError(1, ["./run_format.sh"], stderr="Command failed")

        # Create a config file with format command
        format_command = ["./run_format.sh"]
        config = {"commands": {"format": format_command}}
        config_path = os.path.join(self.project_dir, "codemcp.toml")
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        result = format_code(self.project_dir)
        self.assertIn("Error", result)

    @patch("codemcp.tools.format.is_git_repository")
    def test_format_code_no_command(self, mock_is_git_repo):
        """Test format_code when no format command is configured."""
        # Mock git repository check
        mock_is_git_repo.return_value = False

        # Create a config file without format command
        config = {"global_prompt": "Test prompt"}
        config_path = os.path.join(self.project_dir, "codemcp.toml")
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        result = format_code(self.project_dir)
        self.assertIn("Error: No format command configured", result)

    @patch("codemcp.tools.format.is_git_repository")
    def test_format_code_invalid_directory(self, mock_is_git_repo):
        """Test format_code with a non-existent directory."""
        # This mock shouldn't be called as the directory check happens first
        result = format_code("/nonexistent/directory")
        self.assertIn("Error: Directory does not exist", result)
        mock_is_git_repo.assert_not_called()

    @patch("codemcp.tools.format.run_command")
    def test_check_for_changes(self, mock_run):
        """Test _check_for_changes function."""
        # Test case 1: Changes detected
        mock_process1 = MagicMock()
        mock_process1.stdout = " M file1.py\n?? file2.py\n"
        mock_process1.stderr = ""

        # Test case 2: No changes detected
        mock_process2 = MagicMock()
        mock_process2.stdout = ""
        mock_process2.stderr = ""

        # Test case 3: Exception occurs
        mock_run.side_effect = [mock_process1, mock_process2, Exception("Git error")]

        # Test with changes
        result1 = _check_for_changes(self.project_dir)
        self.assertTrue(result1)

        # Test without changes
        result2 = _check_for_changes(self.project_dir)
        self.assertFalse(result2)

        # Test with exception
        result3 = _check_for_changes(self.project_dir)
        self.assertFalse(result3)

        # Verify run_command was called correctly
        calls = [
            call(
                ["git", "status", "--porcelain"],
                cwd=self.project_dir,
                check=True,
                capture_output=True,
                text=True,
            ),
            call(
                ["git", "status", "--porcelain"],
                cwd=self.project_dir,
                check=True,
                capture_output=True,
                text=True,
            ),
        ]
        mock_run.assert_has_calls(calls)

    @patch("codemcp.tools.format.commit_changes")
    @patch("codemcp.tools.format._check_for_changes")
    @patch("codemcp.tools.format.is_git_repository")
    @patch("codemcp.tools.format.run_command")
    def test_format_code_with_git_changes(
        self, mock_run, mock_is_git_repo, mock_check_changes, mock_commit
    ):
        """Test format_code when it makes changes in a git repository."""
        # Mock git repository check
        mock_is_git_repo.return_value = True

        # Mock changes before (no changes) and after (changes detected)
        mock_check_changes.side_effect = [False, True]

        # Mock successful commit
        mock_commit.return_value = (True, "Changes committed successfully")

        # Mock successful subprocess run
        mock_process = MagicMock()
        mock_process.stdout = "Formatting successful"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Create a config file with format command
        format_command = ["./run_format.sh"]
        config = {"commands": {"format": format_command}}
        config_path = os.path.join(self.project_dir, "codemcp.toml")
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        result = format_code(self.project_dir)
        self.assertIn("Code formatting successful and changes committed", result)

        # Verify run_command was called for the format command
        mock_run.assert_called_once()

        # Verify commit_changes was called
        mock_commit.assert_called_once_with(
            self.project_dir, "Auto-commit formatting changes"
        )

    @patch("codemcp.tools.format.commit_changes")
    @patch("codemcp.tools.format._check_for_changes")
    @patch("codemcp.tools.format.is_git_repository")
    @patch("codemcp.tools.format.run_command")
    def test_format_code_with_git_changes_commit_failure(
        self, mock_run, mock_is_git_repo, mock_check_changes, mock_commit
    ):
        """Test format_code when it makes changes in a git repository but commit fails."""
        # Mock git repository check
        mock_is_git_repo.return_value = True

        # Mock changes before (no changes) and after (changes detected)
        mock_check_changes.side_effect = [False, True]

        # Mock failed commit
        mock_commit.return_value = (
            False,
            "Failed to commit changes: no user.email configured",
        )

        # Mock successful subprocess run
        mock_process = MagicMock()
        mock_process.stdout = "Formatting successful"
        mock_process.stderr = ""
        mock_run.return_value = mock_process

        # Create a config file with format command
        format_command = ["./run_format.sh"]
        config = {"commands": {"format": format_command}}
        config_path = os.path.join(self.project_dir, "codemcp.toml")
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        result = format_code(self.project_dir)
        self.assertIn("Code formatting successful but failed to commit changes", result)
        self.assertIn("Failed to commit changes", result)

        # Verify run_command was called for the format command
        mock_run.assert_called_once()

        # Verify commit_changes was called
        mock_commit.assert_called_once_with(
            self.project_dir, "Auto-commit formatting changes"
        )


if __name__ == "__main__":
    unittest.main()
