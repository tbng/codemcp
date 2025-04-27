#!/usr/bin/env python3

import os
import subprocess
import sys
import tempfile

import pytest

from codemcp.main import init_codemcp_project


@pytest.fixture
def project_dir():
    """Create a temporary project directory with a simple codemcp.toml configuration."""
    with tempfile.TemporaryDirectory() as temp_dir:
        # Initialize the project
        init_codemcp_project(temp_dir)

        # Create a codemcp.toml file with test commands
        config_path = os.path.join(temp_dir, "codemcp.toml")
        with open(config_path, "w") as f:
            f.write("""
[commands]
echo = ["echo", "Hello World"]
list = ["ls", "-la"]
exit_with_error = ["bash", "-c", "exit 1"]
            """)

        yield temp_dir


def test_run_command_exists():
    """Test that the 'run' command exists and is listed in help output."""
    result = subprocess.run(
        [sys.executable, "-m", "codemcp", "--help"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "run" in result.stdout


def test_run_command_basic(project_dir):
    """Test running a basic command that outputs to stdout."""
    result = subprocess.run(
        [sys.executable, "-m", "codemcp", "run", "echo", "--path", project_dir],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "Hello World" in result.stdout


def test_run_command_with_args(project_dir):
    """Test running a command with additional arguments that override defaults."""
    # Create a file to list
    test_file = os.path.join(project_dir, "test_file.txt")
    with open(test_file, "w") as f:
        f.write("test content")

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "codemcp",
            "run",
            "list",
            test_file,
            "--path",
            project_dir,
        ],
        capture_output=True,
        text=True,
        check=True,
    )
    assert "test_file.txt" in result.stdout


def test_run_command_error_exit_code(project_dir):
    """Test that error exit codes from the command are propagated."""
    # This should return a non-zero exit code
    process = subprocess.run(
        [
            sys.executable,
            "-m",
            "codemcp",
            "run",
            "exit_with_error",
            "--path",
            project_dir,
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode != 0


def test_run_command_missing_command(project_dir):
    """Test running a command that doesn't exist in codemcp.toml."""
    process = subprocess.run(
        [sys.executable, "-m", "codemcp", "run", "nonexistent", "--path", project_dir],
        capture_output=True,
        text=True,
        check=False,
    )
    assert process.returncode != 0
    assert "not found in codemcp.toml" in process.stderr
