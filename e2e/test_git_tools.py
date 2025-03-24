#!/usr/bin/env python3

import asyncio
import os
import shutil
import tempfile
import unittest
from unittest import mock

from codemcp.shell import run_command
from codemcp.tools.git_blame import git_blame
from codemcp.tools.git_diff import git_diff
from codemcp.tools.git_log import git_log
from codemcp.tools.git_show import git_show


class TestGitTools(unittest.TestCase):
    """Test the git tools functionality."""

    def setUp(self):
        # Create a temporary directory
        self.temp_dir = tempfile.mkdtemp()

        # Initialize a git repository
        asyncio.run(self.async_setup())

    async def async_setup(self):
        # Initialize a git repository
        await run_command(
            cmd=["git", "init"], cwd=self.temp_dir, capture_output=True, text=True
        )

        # Create a sample file
        self.sample_file = os.path.join(self.temp_dir, "sample.txt")
        with open(self.sample_file, "w") as f:
            f.write("Sample content\nLine 2\nLine 3\n")

        # Add and commit the file
        await run_command(
            cmd=["git", "config", "user.name", "Test User"],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
        )
        await run_command(
            cmd=["git", "config", "user.email", "test@example.com"],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
        )
        await run_command(
            cmd=["git", "add", "sample.txt"],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
        )
        await run_command(
            cmd=["git", "commit", "-m", "Initial commit"],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
        )

        # Modify the file and create another commit
        with open(self.sample_file, "a") as f:
            f.write("Line 4\nLine 5\n")

        await run_command(
            cmd=["git", "add", "sample.txt"],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
        )
        await run_command(
            cmd=["git", "commit", "-m", "Second commit"],
            cwd=self.temp_dir,
            capture_output=True,
            text=True,
        )

    def tearDown(self):
        # Clean up the temporary directory
        shutil.rmtree(self.temp_dir)

    def test_git_log(self):
        """Test the git_log tool."""

        async def _test():
            # Test with no arguments
            result = await git_log(path=self.temp_dir)
            self.assertIn("Initial commit", result["output"])
            self.assertIn("Second commit", result["output"])

            # Test with arguments
            result = await git_log(arguments="--oneline -n 1", path=self.temp_dir)
            self.assertIn("Second commit", result["output"])
            self.assertNotIn("Initial commit", result["output"])

        asyncio.run(_test())

    def test_git_diff(self):
        """Test the git_diff tool."""

        async def _test():
            # Create a change but don't commit it
            with open(self.sample_file, "a") as f:
                f.write("Uncommitted change\n")

            # Test with no arguments
            result = await git_diff(path=self.temp_dir)
            self.assertIn("Uncommitted change", result["output"])

            # Test with arguments
            result = await git_diff(arguments="HEAD~1 HEAD", path=self.temp_dir)
            self.assertIn("Line 4", result["output"])

        asyncio.run(_test())

    def test_git_show(self):
        """Test the git_show tool."""

        async def _test():
            # Test with no arguments (should show the latest commit)
            result = await git_show(path=self.temp_dir)
            self.assertIn("Second commit", result["output"])

            # Test with arguments
            result = await git_show(arguments="HEAD~1", path=self.temp_dir)
            self.assertIn("Initial commit", result["output"])

        asyncio.run(_test())

    def test_git_blame(self):
        """Test the git_blame tool."""

        async def _test():
            # Test with file argument
            result = await git_blame(arguments="sample.txt", path=self.temp_dir)
            self.assertIn("Test User", result["output"])
            self.assertIn("Line 2", result["output"])

            # Test with line range
            result = await git_blame(arguments="-L 4,5 sample.txt", path=self.temp_dir)
            self.assertIn("Line 4", result["output"])
            self.assertNotIn("Line 2", result["output"])

        asyncio.run(_test())

    def test_invalid_path(self):
        """Test that tools handle invalid paths."""

        async def _test():
            with mock.patch(
                "codemcp.tools.git_log.is_git_repository", return_value=False
            ):
                with self.assertRaises(ValueError):
                    await git_log(path="/invalid/path")

            with mock.patch(
                "codemcp.tools.git_diff.is_git_repository", return_value=False
            ):
                with self.assertRaises(ValueError):
                    await git_diff(path="/invalid/path")

            with mock.patch(
                "codemcp.tools.git_show.is_git_repository", return_value=False
            ):
                with self.assertRaises(ValueError):
                    await git_show(path="/invalid/path")

            with mock.patch(
                "codemcp.tools.git_blame.is_git_repository", return_value=False
            ):
                with self.assertRaises(ValueError):
                    await git_blame(path="/invalid/path")

        asyncio.run(_test())

    def test_command_failure(self):
        """Test that tools handle command failures."""

        async def _test():
            # Test with invalid arguments
            result = await git_log(arguments="--invalid-option", path=self.temp_dir)
            self.assertIn("Error", result["resultForAssistant"])

            result = await git_diff(arguments="--invalid-option", path=self.temp_dir)
            self.assertIn("Error", result["resultForAssistant"])

            result = await git_show(arguments="--invalid-option", path=self.temp_dir)
            self.assertIn("Error", result["resultForAssistant"])

            result = await git_blame(arguments="--invalid-option", path=self.temp_dir)
            self.assertIn("Error", result["resultForAssistant"])

        asyncio.run(_test())
