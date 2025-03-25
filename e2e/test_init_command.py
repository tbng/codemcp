#!/usr/bin/env python3

import subprocess
import tempfile
from pathlib import Path

from codemcp.main import init_codemcp_project


def test_init_command():
    """Test the init command creates a codemcp.toml file and initializes a git repo."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Run the init_codemcp_project function
        result = init_codemcp_project(temp_dir)

        # Check that the function reports success
        assert "Successfully initialized" in result

        # Check that codemcp.toml was created
        config_file = Path(temp_dir) / "codemcp.toml"
        assert config_file.exists()

        # Check that git repository was initialized
        git_dir = Path(temp_dir) / ".git"
        assert git_dir.is_dir()

        # Check that a commit was created
        result = subprocess.run(
            ["git", "log", "--oneline"],
            cwd=temp_dir,
            capture_output=True,
            text=True,
            check=True,
        )
        assert "initialize codemcp project" in result.stdout


def test_init_command_existing_repo():
    """Test the init command works with an existing git repository."""
    # Create a temporary directory for testing
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize git repository first
        subprocess.run(["git", "init"], cwd=temp_dir, check=True)

        # Make a dummy commit to simulate existing repository
        dummy_file = Path(temp_dir) / "dummy.txt"
        dummy_file.write_text("test content")

        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=temp_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"],
            cwd=temp_dir,
            check=True,
        )
        subprocess.run(["git", "add", "dummy.txt"], cwd=temp_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], cwd=temp_dir, check=True
        )

        # Run the init_codemcp_project function
        result = init_codemcp_project(temp_dir)

        # Check that the function reports success
        assert "Successfully initialized" in result

        # Check that codemcp.toml was created
        config_file = Path(temp_dir) / "codemcp.toml"
        assert config_file.exists()
