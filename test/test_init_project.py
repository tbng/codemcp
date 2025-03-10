#!/usr/bin/env python3

import os
import tempfile
import unittest
from pathlib import Path

from codemcp.tools import init_project


class InitProjectTestCase(unittest.TestCase):
    def setUp(self):
        # Create a temporary directory for testing
        self.test_dir = tempfile.TemporaryDirectory()
        self.dir_path = self.test_dir.name

    def tearDown(self):
        # Clean up temporary directory
        self.test_dir.cleanup()

    def test_init_project_no_rules_file(self):
        """Test initializing a project without a codemcp.toml file."""
        result = init_project(self.dir_path)
        self.assertEqual(result, "Do NOT attempt to run tests, let the user run them.")

    def test_init_project_with_rules_file(self):
        """Test initializing a project with a codemcp.toml file."""
        # Create a codemcp.toml file with a global_prompt
        rules_file_path = os.path.join(self.dir_path, "codemcp.toml")
        with open(rules_file_path, "w") as f:
            f.write('global_prompt = "This is a custom global prompt."\n')

        result = init_project(self.dir_path)
        expected = "Do NOT attempt to run tests, let the user run them.\n\nThis is a custom global prompt."
        self.assertEqual(result, expected)

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
            f.write('global_prompt = "This is an invalid TOML file\n')  # Missing closing quote

        result = init_project(self.dir_path)
        self.assertTrue(result.startswith("Error reading codemcp.toml file"))


if __name__ == "__main__":
    unittest.main()
