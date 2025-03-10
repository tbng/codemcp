#!/usr/bin/env python3

import os
import tempfile
import unittest
from unittest.mock import patch, MagicMock, call

import tomli_w

from codemcp.tools.format import format_code, _get_format_command, _check_for_changes


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
    @patch("subprocess.run")
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
        
        # Check that subprocess.run was called correctly for the format command
        mock_run.assert_called_once_with(
            format_command,
            cwd=self.project_dir,
            check=True,
            capture_output=True,
            text=True,
        )

    @patch("subprocess.run")
    def test_format_code_failure(self, mock_run):
        """Test format_code when the command fails."""
        # Mock failed subprocess run
        mock_run.side_effect = Exception("Command failed")

        # Create a config file with format command
        format_command = ["./run_format.sh"]
        config = {"commands": {"format": format_command}}
        config_path = os.path.join(self.project_dir, "codemcp.toml")
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        result = format_code(self.project_dir)
        self.assertIn("Error", result)

    def test_format_code_no_command(self):
        """Test format_code when no format command is configured."""
        # Create a config file without format command
        config = {"global_prompt": "Test prompt"}
        config_path = os.path.join(self.project_dir, "codemcp.toml")
        with open(config_path, "wb") as f:
            tomli_w.dump(config, f)

        result = format_code(self.project_dir)
        self.assertIn("Error: No format command configured", result)

    def test_format_code_invalid_directory(self):
        """Test format_code with a non-existent directory."""
        result = format_code("/nonexistent/directory")
        self.assertIn("Error: Directory does not exist", result)


if __name__ == "__main__":
    unittest.main()
