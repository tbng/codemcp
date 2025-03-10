#!/usr/bin/env python3

import os
import tempfile
import unittest
from unittest.mock import patch

from codemcp.tools.init_project import init_project


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

    def test_init_project_no_rules_file(self):
        """Test initializing a project without a codemcp.toml file."""
        result = init_project(self.dir_path)
        # Check for a stable part of the system prompt instead of the exact string
        self.assertIn("# Tests", result)
        self.assertIn("We do NOT support running tests", result)

    def test_init_project_with_rules_file(self):
        """Test initializing a project with a codemcp.toml file."""
        # Create a codemcp.toml file with a global_prompt
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write('global_prompt = "This is a custom global prompt."\n')

        result = init_project(self.dir_path)
        # Check for a stable part of the system prompt and the custom global prompt
        self.assertIn("# Tests", result)
        self.assertIn("We do NOT support running tests", result)
        self.assertIn("This is a custom global prompt.", result)

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
                'global_prompt = "This is an invalid TOML file\n',
            )  # Missing closing quote

        result = init_project(self.dir_path)
        self.assertTrue(result.startswith("Error reading codemcp.toml file"))

    def test_format_not_exposed_when_not_configured(self):
        """Test that the format command is not exposed in the system prompt when no formatter is configured."""
        # Create a codemcp.toml file without format command
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write(
                'global_prompt = "This is a global prompt without formatter config."\n'
            )

        result = init_project(self.dir_path)
        self.assertIn("This is a global prompt without formatter config.", result)
        self.assertNotIn("run code formatting using the Format tool", result)

    def test_format_exposed_when_configured(self):
        """Test that the format command is exposed in the system prompt when a formatter is configured."""
        # Create a codemcp.toml file with format command
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write("""
global_prompt = "This is a global prompt with formatter config."
[commands]
format = ["./run_format.sh"]
""")

        result = init_project(self.dir_path)
        self.assertIn("This is a global prompt with formatter config.", result)
        self.assertIn("run code formatting using the Format tool", result)


if __name__ == "__main__":
    unittest.main()
