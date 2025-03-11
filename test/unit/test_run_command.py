#!/usr/bin/env python3

import os
import tempfile
import subprocess
from unittest.mock import MagicMock, patch

from expecttest import TestCase

from codemcp.tools.code_command import check_for_changes, get_command_from_config
from codemcp.tools.run_command import run_command


class TestRunCommand(TestCase):
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

    def create_config_file(self, command_type="format", command=None):
        """Create a test codemcp.toml file with the specified command"""
        config_path = os.path.join(self.temp_dir.name, "codemcp.toml")

        if command is None:
            command = [f"./run_{command_type}.sh"]

        config_content = "[commands]\n"
        if command:
            command_str = str(command).replace("'", '"')
            config_content += f"{command_type} = {command_str}\n"

        with open(config_path, "w") as f:
            f.write(config_content)

        return config_path
