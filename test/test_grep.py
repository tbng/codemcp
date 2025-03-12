#!/usr/bin/env python3

import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import asyncio

from codemcp.tools.grep import grep_files, git_grep

# Helper function for running async tests
def async_test(coro):
    def wrapper(*args, **kwargs):
        return asyncio.run(coro(*args, **kwargs))
    return wrapper


@async_test
async def test_git_grep_directory():
    """Test git grep with a directory path."""
    with patch("codemcp.git.is_git_repository", new=AsyncMock(return_value=True)), patch(
        "codemcp.shell.run_command",
        new=AsyncMock(
            return_value=MagicMock(
                returncode=0, stdout="file1.py\nfile2.py\nfile3.py", stderr=""
            )
        ),
    ), patch(
        "os.path.exists", return_value=True
    ), patch(
        "os.path.isdir", return_value=True
    ):
        result = await git_grep("pattern", "/test/path")
        assert result == [
            "/test/path/file1.py",
            "/test/path/file2.py",
            "/test/path/file3.py",
        ]


@async_test
async def test_git_grep_file():
    """Test git grep with a file path."""
    with patch("codemcp.git.is_git_repository", new=AsyncMock(return_value=True)), patch(
        "codemcp.shell.run_command",
        new=AsyncMock(
            return_value=MagicMock(
                returncode=0, stdout="file1.py", stderr=""
            )
        ),
    ), patch(
        "os.path.exists", return_value=True
    ), patch(
        "os.path.isdir", return_value=False
    ), patch(
        "os.path.isfile", return_value=True
    ):
        result = await git_grep("pattern", "/test/path/file1.py")
        assert result == ["/test/path/file1.py"]


@async_test
async def test_grep_files_with_file():
    """Test grep_files function with a file path."""
    with patch(
        "codemcp.tools.grep.git_grep",
        new=AsyncMock(return_value=["/test/path/file1.py"]),
    ), patch(
        "os.stat", return_value=MagicMock(st_mtime=1234567890)
    ), patch(
        "os.path.exists", return_value=True
    ):
        result = await grep_files("pattern", "/test/path/file1.py")
        assert result["numFiles"] == 1
        assert result["filenames"] == ["/test/path/file1.py"]
