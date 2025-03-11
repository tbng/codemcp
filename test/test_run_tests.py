#!/usr/bin/env python3

import os
import subprocess
import tempfile
import unittest
from unittest import mock

from codemcp.tools.run_tests import run_tests


class RunTestsTestCase(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.project_dir = self.temp_dir.name

        # Create a mock codemcp.toml file
        os.makedirs(self.project_dir, exist_ok=True)
        with open(os.path.join(self.project_dir, "codemcp.toml"), "w") as f:
            f.write("""global_prompt = "Test Prompt"

[commands]
test = ["./run_test.sh"]
""")

    def tearDown(self):
        self.temp_dir.cleanup()

    @mock.patch("codemcp.tools.run_tests.run_command")
    def test_run_tests_success(self, mock_run_command):
        # Mock the subprocess.run to return success
        mock_process = mock.Mock()
        mock_process.stdout = "Tests passed successfully"
        mock_process.stderr = ""
        mock_run_command.return_value = mock_process

        # Run the test function
        result = run_tests(self.project_dir)

        # Verify run_command was called with the correct arguments
        mock_run_command.assert_called_once_with(
            ["./run_test.sh"],
            cwd=self.project_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        # Verify the result
        self.assertIn("Tests completed successfully", result)
        self.assertIn("Tests passed successfully", result)

    @mock.patch("codemcp.tools.run_tests.run_command")
    def test_run_tests_with_selector(self, mock_run_command):
        # Mock the subprocess.run to return success
        mock_process = mock.Mock()
        mock_process.stdout = "Selected tests passed"
        mock_process.stderr = ""
        mock_run_command.return_value = mock_process

        # Run the test function with a selector
        result = run_tests(self.project_dir, "test_specific")

        # Verify run_command was called with the correct arguments including the selector
        mock_run_command.assert_called_once_with(
            ["./run_test.sh", "test_specific"],
            cwd=self.project_dir,
            check=True,
            capture_output=True,
            text=True,
        )

        # Verify the result
        self.assertIn("Tests completed successfully", result)
        self.assertIn("Selected tests passed", result)

    @mock.patch("codemcp.tools.run_tests.run_command")
    def test_run_tests_failure(self, mock_run_command):
        # Create a CalledProcessError with appropriate attributes
        error = subprocess.CalledProcessError(1, ["./run_test.sh"])
        error.stdout = "Some tests failed"
        error.stderr = "Error in tests"
        mock_run_command.side_effect = error

        # Run the test function
        result = run_tests(self.project_dir)

        # Verify run_command was called
        mock_run_command.assert_called_once()

        # Verify the result
        self.assertIn("Tests failed", result)
        self.assertIn("Some tests failed", result)
        self.assertIn("Error in tests", result)

    def test_run_tests_no_config(self):
        # Remove the codemcp.toml file
        os.remove(os.path.join(self.project_dir, "codemcp.toml"))

        # Run the test function
        result = run_tests(self.project_dir)

        # Verify the result
        self.assertIn("Error: No test command configured", result)

    def test_run_tests_invalid_directory(self):
        # Test with a non-existent directory
        result = run_tests("/path/that/does/not/exist")

        # Verify the result
        self.assertIn("Error: Directory does not exist", result)


if __name__ == "__main__":
    unittest.main()
