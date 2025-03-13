#!/usr/bin/env python3

import os
import pytest
import tempfile
from pathlib import Path

from conftest import run_codemcp


@pytest.fixture
def temp_project():
    """Create a temporary directory with test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a simple git repository
        os.system(f"cd {tmpdir} && git init")

        # Create test files with various extensions
        for ext in ["js", "py", "md", "txt", "json"]:
            # Create files in the root
            with open(os.path.join(tmpdir, f"file1.{ext}"), "w") as f:
                f.write(f"Test content for file1.{ext}")

            # Create nested directory structure
            nested_dir = os.path.join(tmpdir, "src", "nested")
            os.makedirs(nested_dir, exist_ok=True)

            with open(os.path.join(nested_dir, f"file2.{ext}"), "w") as f:
                f.write(f"Test content for file2.{ext}")

        # Create codemcp.toml file
        with open(os.path.join(tmpdir, "codemcp.toml"), "w") as f:
            f.write("[tool.codemcp]\nversion = 1\n")

        # Commit the files
        os.system(
            f"cd {tmpdir} && git add . && git config user.email 'test@example.com' && git config user.name 'Test User' && git commit -m 'Initial commit'"
        )

        yield tmpdir


def test_glob_basic(temp_project):
    """Test basic glob functionality."""
    # Find all JavaScript files
    output = run_codemcp(
        "codemcp",
        ["Glob", "*.js", temp_project],
        "test-glob-basic",
    )

    # Verify output contains the js file in the root directory
    root_js_file = os.path.join(temp_project, "file1.js")
    assert root_js_file in output

    # Verify the count is correct
    assert "Found 1 file" in output


def test_glob_recursive(temp_project):
    """Test recursive glob search."""
    # Find all Python files recursively
    output = run_codemcp(
        "codemcp",
        ["Glob", "**/*.py", temp_project],
        "test-glob-recursive",
    )

    # Verify both Python files are found
    root_py_file = os.path.join(temp_project, "file1.py")
    nested_py_file = os.path.join(temp_project, "src", "nested", "file2.py")

    assert root_py_file in output
    assert nested_py_file in output

    # Verify the count is correct
    assert "Found 2 file" in output


def test_glob_with_no_matches(temp_project):
    """Test glob with no matching files."""
    # Search for a non-existent file pattern
    output = run_codemcp(
        "codemcp",
        ["Glob", "*.xyz", temp_project],
        "test-glob-no-matches",
    )

    # Verify correct output
    assert "No files found" in output


def test_glob_with_nested_search(temp_project):
    """Test glob searching in nested directory."""
    # Search only in nested directory
    nested_dir = os.path.join(temp_project, "src", "nested")
    output = run_codemcp(
        "codemcp",
        ["Glob", "*.md", nested_dir],
        "test-glob-nested",
    )

    # Verify only the nested markdown file is found
    root_md_file = os.path.join(temp_project, "file1.md")
    nested_md_file = os.path.join(nested_dir, "file2.md")

    assert root_md_file not in output
    assert nested_md_file in output

    # Verify the count is correct
    assert "Found 1 file" in output


def test_glob_with_multiple_patterns(temp_project):
    """Test glob with multiple patterns using brace expansion."""
    # Find all JSON and TXT files
    output = run_codemcp(
        "codemcp",
        ["Glob", "**/*.{json,txt}", temp_project],
        "test-glob-multiple-patterns",
    )

    # Verify the expected files are found
    root_json_file = os.path.join(temp_project, "file1.json")
    root_txt_file = os.path.join(temp_project, "file1.txt")
    nested_json_file = os.path.join(temp_project, "src", "nested", "file2.json")
    nested_txt_file = os.path.join(temp_project, "src", "nested", "file2.txt")

    assert root_json_file in output
    assert root_txt_file in output
    assert nested_json_file in output
    assert nested_txt_file in output

    # Verify the count is correct
    assert "Found 4 file" in output


def test_glob_with_invalid_path(temp_project):
    """Test glob with an invalid path."""
    # Try to search in a non-existent directory
    invalid_path = os.path.join(temp_project, "nonexistent")
    output = run_codemcp(
        "codemcp",
        ["Glob", "*.py", invalid_path],
        "test-glob-invalid-path",
    )

    # Verify error message
    assert "Error" in output
    assert "Path does not exist" in output


def test_glob_with_limit_and_offset(temp_project):
    """Test glob with limit and offset parameters."""
    # Create more files to test pagination
    for i in range(10):
        with open(os.path.join(temp_project, f"extra{i}.log"), "w") as f:
            f.write(f"Extra log file {i}")

    # Commit the additional files
    os.system(f"cd {temp_project} && git add . && git commit -m 'Add extra files'")

    # Test with limit
    output_limited = run_codemcp(
        "codemcp",
        ["Glob", "*.log", temp_project, "--limit=5"],
        "test-glob-limit",
    )

    # Verify only 5 files are returned
    log_files = [line for line in output_limited.splitlines() if line.endswith(".log")]
    assert len(log_files) == 5

    # Test with offset
    output_offset = run_codemcp(
        "codemcp",
        ["Glob", "*.log", temp_project, "--offset=5"],
        "test-glob-offset",
    )

    # Verify different files are returned with offset
    offset_log_files = [
        line for line in output_offset.splitlines() if line.endswith(".log")
    ]
    assert set(log_files) != set(offset_log_files)
