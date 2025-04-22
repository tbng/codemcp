#!/usr/bin/env python3

import subprocess
import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from codemcp.main import cli


@pytest.fixture
def test_project():
    """Create a temporary directory with a codemcp.toml file for testing."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create a codemcp.toml file with test commands
        config_path = Path(tmp_dir) / "codemcp.toml"
        with open(config_path, "w") as f:
            f.write("""[commands]
echo = ["echo", "Hello from codemcp run!"]
echo_args = ["echo"]
invalid = []
""")

        # Initialize a git repository
        subprocess.run(["git", "init"], cwd=tmp_dir, check=True, capture_output=True)
        subprocess.run(
            ["git", "config", "user.name", "Test User"], cwd=tmp_dir, check=True
        )
        subprocess.run(
            ["git", "config", "user.email", "test@example.com"], cwd=tmp_dir, check=True
        )
        subprocess.run(["git", "add", "codemcp.toml"], cwd=tmp_dir, check=True)
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], cwd=tmp_dir, check=True
        )

        yield tmp_dir


def test_run_command_success(test_project):
    """Test running a command successfully."""
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "echo", "--path", test_project])

    assert result.exit_code == 0
    assert "Hello from codemcp run!" in result.output
    assert "Code echo successful" in result.output


def test_run_command_with_args(test_project):
    """Test running a command with arguments."""
    runner = CliRunner()
    result = runner.invoke(
        cli, ["run", "echo_args", "Test", "argument", "string", "--path", test_project]
    )

    assert result.exit_code == 0
    assert "Test argument string" in result.output
    assert "Code echo_args successful" in result.output


def test_run_command_not_found(test_project):
    """Test running a command that doesn't exist in config."""
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "nonexistent", "--path", test_project])

    assert "Error: Command 'nonexistent' not found in codemcp.toml" in result.output


def test_run_command_empty_definition(test_project):
    """Test running a command with an empty definition."""
    runner = CliRunner()
    result = runner.invoke(cli, ["run", "invalid", "--path", test_project])

    assert "Error: Command 'invalid' not found in codemcp.toml" in result.output
