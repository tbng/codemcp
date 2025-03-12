#!/usr/bin/env python3

import os
import tempfile
import unittest
from unittest.mock import mock_open, patch

from codemcp.tools.init_project import _generate_chat_id, init_project


class InitProjectTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.dir_path = self.test_dir.name

        # Setup mock patches
        self.setup_mocks()

    def tearDown(self):
        # Clean up temporary directory
        self.test_dir.cleanup()

    def setup_mocks(self):
        """Setup mocks for git functions to bypass repository checks"""
        # Create patch for git repository check
        self.is_git_repo_patch = patch("codemcp.git.is_git_repository")
        self.mock_is_git_repo = self.is_git_repo_patch.start()
        self.mock_is_git_repo.return_value = True
        self.addCleanup(self.is_git_repo_patch.stop)

        # Create patch for git base directory
        self.git_base_dir_patch = patch("codemcp.access.get_git_base_dir")
        self.mock_git_base_dir = self.git_base_dir_patch.start()
        self.mock_git_base_dir.return_value = self.dir_path
        self.addCleanup(self.git_base_dir_patch.stop)

        # Create patch for git repository root
        self.git_repo_root_patch = patch(
            "codemcp.tools.init_project.get_repository_root"
        )
        self.mock_git_repo_root = self.git_repo_root_patch.start()
        self.mock_git_repo_root.return_value = self.dir_path
        self.addCleanup(self.git_repo_root_patch.stop)

    def test_init_project_no_rules_file(self):
        """Test initializing a project without a codemcp.toml file."""
        result = init_project(self.dir_path)
        # Check for a stable part of the system prompt instead of the exact string
        self.assertIn("# Tone and style", result)
        self.assertIn("# Following conventions", result)
        # Check that a chat ID was generated
        self.assertIn("This chat has been assigned a unique ID:", result)

    def test_init_project_with_rules_file(self):
        """Test initializing a project with a codemcp.toml file."""
        # Create a codemcp.toml file with a project_prompt
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write('project_prompt = "This is a custom global prompt."\n')

        result = init_project(self.dir_path)
        # Check for a stable part of the system prompt and the custom global prompt
        self.assertIn("# Tone and style", result)
        self.assertIn("# Following conventions", result)
        self.assertIn("This is a custom global prompt.", result)
        # Check that a chat ID was generated
        self.assertIn("This chat has been assigned a unique ID:", result)

    def test_init_project_invalid_directory(self):
        """Test initializing a project with an invalid directory."""
        result = init_project("/this/directory/does/not/exist")
        self.assertTrue(result.startswith("Error: Directory does not exist"))

    def test_init_project_not_a_directory(self):
        """Test initializing a project with a path that is not a directory."""
        # Create a file
        test_file = os.path.join(self.dir_path, "test_file.txt")
        with open(test_file, "w") as f:
            f.write("This is a test file")

        result = init_project(test_file)
        self.assertTrue(result.startswith("Error: Path is not a directory"))

    def test_init_project_invalid_toml(self):
        """Test initializing a project with an invalid TOML file."""
        # Create an invalid codemcp.toml file
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write(
                'project_prompt = "This is an invalid TOML file\n',
            )  # Missing closing quote

        result = init_project(self.dir_path)
        self.assertTrue(result.startswith("Error reading codemcp.toml file"))

    def test_format_not_exposed_when_not_configured(self):
        """Test that the format command is not exposed in the system prompt when no formatter is configured."""
        # Create a codemcp.toml file without format command
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write(
                'project_prompt = "This is a global prompt without formatter config."\n'
            )

        result = init_project(self.dir_path)
        self.assertIn("This is a global prompt without formatter config.", result)
        self.assertNotIn("run code formatting using the Format tool", result)

    def test_command_docs_exposed_when_configured(self):
        """Test that command documentation is included in the system prompt when configured."""
        # Create a codemcp.toml file with command documentation
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write("""
project_prompt = "This is a global prompt with command docs."
[commands]
format = ["./run_format.sh"]
[commands.test]
command = ["./run_test.sh"]
doc = "Accepts a pytest-style test selector as an argument to run a specific test."
""")

        result = init_project(self.dir_path)
        self.assertIn("This is a global prompt with command docs.", result)
        self.assertIn("Command documentation:", result)
        self.assertIn(
            "- test: Accepts a pytest-style test selector as an argument to run a specific test.",
            result,
        )

    def test_multiple_command_docs(self):
        """Test handling of multiple command documentations."""
        # Create a codemcp.toml file with multiple command documentations
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write("""
project_prompt = "This is a global prompt with multiple command docs."
[commands]
format = ["./run_format.sh"]
[commands.test]
command = ["./run_test.sh"]
doc = "Accepts a pytest-style test selector."
[commands.lint]
command = ["./run_lint.sh"]
doc = "Runs linting tools on the codebase."
""")

        result = init_project(self.dir_path)
        self.assertIn("This is a global prompt with multiple command docs.", result)
        self.assertIn("Command documentation:", result)
        self.assertIn("- test: Accepts a pytest-style test selector.", result)
        self.assertIn("- lint: Runs linting tools on the codebase.", result)

    def test_no_command_docs(self):
        """Test that no command documentation is included when none is configured."""
        # Create a codemcp.toml file without command documentation
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write("""
project_prompt = "This is a global prompt without command docs."
[commands]
format = ["./run_format.sh"]
test = ["./run_test.sh"]
""")

        result = init_project(self.dir_path)
        self.assertIn("This is a global prompt without command docs.", result)
        self.assertNotIn("Command documentation:", result)

    def test_chat_id_generation(self):
        """Test that the chat ID generation works as expected."""
        # Mock the open function for reading and writing the counter file
        with patch("builtins.open", mock_open(read_data="42")) as mock_file:
            chat_id = _generate_chat_id(self.dir_path)

            # Check the format of the chat ID
            self.assertTrue(
                chat_id.startswith("43-"),
                f"Expected chat ID to start with '43-', got {chat_id}",
            )

            # Verify that the counter file was read and written
            mock_file.assert_any_call(
                os.path.join(self.dir_path, ".git", "codemcp", "counter"), "r"
            )
            mock_file.assert_any_call(
                os.path.join(self.dir_path, ".git", "codemcp", "counter"), "w"
            )

            # Verify that the counter was incremented and written back
            handle = mock_file()
            handle.write.assert_called_once_with("43")

    def test_chat_id_generation_no_counter(self):
        """Test chat ID generation when no counter file exists."""
        # Mock os.path.exists to return False for the counter file
        with patch("os.path.exists", return_value=False):
            # Mock the open function for writing the counter file
            with patch("builtins.open", mock_open()) as mock_file:
                chat_id = _generate_chat_id(self.dir_path)

                # Check the format of the chat ID
                self.assertTrue(
                    chat_id.startswith("1-"),
                    f"Expected chat ID to start with '1-', got {chat_id}",
                )

                # Verify that the counter file was written with initial value 1
                handle = mock_file()
                handle.write.assert_called_once_with("1")

    def test_chat_id_generation_not_git_repo(self):
        """Test chat ID generation when not in a git repository."""
        # Mock is_git_repository to return False
        self.mock_is_git_repo.return_value = False

        chat_id = _generate_chat_id(self.dir_path)

        # Check the format of the chat ID (should use fallback value 0)
        self.assertTrue(
            chat_id.startswith("0-"),
            f"Expected chat ID to start with '0-', got {chat_id}",
        )


if __name__ == "__main__":
    unittest.main()
