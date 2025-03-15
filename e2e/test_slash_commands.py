#!/usr/bin/env python3

import tempfile
from pathlib import Path
from unittest import IsolatedAsyncioTestCase
from unittest.mock import patch

from expecttest import TestCase

from codemcp.tools.user_prompt import user_prompt


class TestSlashCommands(IsolatedAsyncioTestCase, TestCase):
    """Test the slash commands functionality."""

    def setUp(self):
        # Create temporary directories for project and global command directories
        self.project_temp_dir = tempfile.TemporaryDirectory()
        self.global_temp_dir = tempfile.TemporaryDirectory()

        # Create the command directories
        self.project_commands_dir = (
            Path(self.project_temp_dir.name) / ".claude" / "commands"
        )
        self.global_commands_dir = (
            Path(self.global_temp_dir.name) / ".claude" / "commands"
        )

        # Make sure the directories exist
        self.project_commands_dir.mkdir(parents=True, exist_ok=True)
        self.global_commands_dir.mkdir(parents=True, exist_ok=True)

    def tearDown(self):
        # Clean up the temporary directories
        self.project_temp_dir.cleanup()
        self.global_temp_dir.cleanup()

    @patch("codemcp.slash_commands.get_commands_directories")
    async def test_slash_command_detection(self, mock_get_dirs):
        """Test that slash commands are correctly detected and returned."""
        # Set up the mock to return our test directories
        mock_get_dirs.return_value = (
            self.project_commands_dir,
            self.global_commands_dir,
        )

        # Create a test command file in the global directory
        test_command_path = self.global_commands_dir / "test.md"
        test_command_content = "This is a test command instruction"
        with open(test_command_path, "w") as f:
            f.write(test_command_content)

        # Test with a prompt containing the command
        result = await user_prompt("Let's use the /test command", "test-chat-id")
        self.assertExpectedInline(result, """This is a test command instruction""")

        # Test with a prompt without any command
        result = await user_prompt("This is a normal prompt", "test-chat-id")
        self.assertExpectedInline(result, """User prompt received""")

    @patch("codemcp.slash_commands.get_commands_directories")
    async def test_project_overrides_global(self, mock_get_dirs):
        """Test that project-specific commands override global commands."""
        # Set up the mock to return our test directories
        mock_get_dirs.return_value = (
            self.project_commands_dir,
            self.global_commands_dir,
        )

        # Create a test command file in both directories
        global_command_path = self.global_commands_dir / "override.md"
        project_command_path = self.project_commands_dir / "override.md"

        with open(global_command_path, "w") as f:
            f.write("Global command")

        with open(project_command_path, "w") as f:
            f.write("Project command")

        # Test that the project command overrides the global one
        result = await user_prompt("Using /override now", "test-chat-id")
        self.assertExpectedInline(result, """Project command""")

    @patch("codemcp.slash_commands.get_commands_directories")
    async def test_command_at_beginning(self, mock_get_dirs):
        """Test that commands at the beginning of the text are detected."""
        # Set up the mock to return our test directories
        mock_get_dirs.return_value = (
            self.project_commands_dir,
            self.global_commands_dir,
        )

        # Create a test command file
        test_command_path = self.global_commands_dir / "begin.md"
        with open(test_command_path, "w") as f:
            f.write("Command at beginning")

        # Test with a prompt starting with the command
        result = await user_prompt("/begin command at the beginning", "test-chat-id")
        self.assertExpectedInline(result, """Command at beginning""")

    @patch("codemcp.slash_commands.get_commands_directories")
    async def test_command_with_hyphen(self, mock_get_dirs):
        """Test that commands with hyphens are properly detected."""
        # Set up the mock to return our test directories
        mock_get_dirs.return_value = (
            self.project_commands_dir,
            self.global_commands_dir,
        )

        # Create a test command file with a hyphen in the name
        test_command_path = self.global_commands_dir / "test-command.md"
        with open(test_command_path, "w") as f:
            f.write("Command with hyphen")

        # Test with a prompt containing the command with hyphen
        result = await user_prompt("Let's try /test-command now", "test-chat-id")
        self.assertExpectedInline(result, """Command with hyphen""")
