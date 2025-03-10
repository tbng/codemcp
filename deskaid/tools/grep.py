#!/usr/bin/env python3

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, List, Optional, Any

from ..common import normalize_file_path
from ..git import is_git_repository

# Define constants
MAX_RESULTS = 100
TOOL_NAME_FOR_PROMPT = "Grep"
DESCRIPTION = f"""
Searches for files containing a specified pattern (regular expression) using git grep.
Files with a match are returned, up to a maximum of {MAX_RESULTS} files.
Note that this tool only works inside git repositories.

Example:
  grep "function.*hello" /path/to/repo  # Find files containing functions with "hello" in their name
  grep "console\\.log" /path/to/repo --include="*.js"  # Find JS files with console.log statements
"""


def git_grep(pattern: str, path: Optional[str] = None, include: Optional[str] = None, signal=None) -> List[str]:
    """Execute git grep to search for pattern in files.

    Args:
        pattern: The regular expression pattern to search for
        path: The directory to search in (must be in a git repository)
        include: Optional file pattern to filter the search
        signal: Optional abort signal to terminate the subprocess

    Returns:
        A list of file paths with matches
    """
    if path is None:
        raise ValueError("Path must be provided for git grep")

    # Normalize the directory path
    absolute_path = normalize_file_path(path)

    # Check if path exists and is a directory
    if not os.path.exists(absolute_path):
        raise FileNotFoundError(f"Directory does not exist: {path}")

    if not os.path.isdir(absolute_path):
        raise NotADirectoryError(f"Path is not a directory: {path}")

    # Verify this is a git repository
    if not is_git_repository(absolute_path):
        raise ValueError(f"The provided path is not in a git repository: {path}")

    # Build git grep command
    # -l: list file names only
    # -i: case insensitive matching
    args = ["git", "grep", "-li", pattern]

    # Add file pattern if specified
    if include:
        args.extend(["--", include])

    logging.debug(f"Executing git grep command: {' '.join(args)}")

    try:
        # Execute git grep command
        result = subprocess.run(
            args,
            cwd=absolute_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            check=False,  # Don't raise exception if git grep doesn't find matches
        )

        # Log command output
        if result.stdout:
            logging.debug(f"git grep stdout: {result.stdout.strip()}")
        if result.stderr:
            logging.debug(f"git grep stderr: {result.stderr.strip()}")

        # git grep returns exit code 1 when no matches are found, which is normal
        if result.returncode not in [0, 1]:
            logging.error(f"git grep failed with exit code {result.returncode}: {result.stderr}")
            raise subprocess.SubprocessError(f"git grep failed: {result.stderr}")

        # Process results - split by newline and filter empty lines
        matches = [line.strip() for line in result.stdout.split('\n') if line.strip()]

        # Convert to absolute paths
        matches = [os.path.join(absolute_path, match) for match in matches]

        return matches
    except subprocess.SubprocessError as e:
        logging.error(f"Error executing git grep: {str(e)}")
        raise


def grep_files(pattern: str, path: Optional[str] = None, include: Optional[str] = None, 
               signal=None) -> Dict[str, Any]:
    """Search for a pattern in files within a directory.

    Args:
        pattern: The regular expression pattern to search for
        path: The directory to search in (must be in a git repository)
        include: Optional file pattern to filter the search
        signal: Optional abort signal to terminate the subprocess

    Returns:
        A dictionary with execution stats and matched files
    """
    start_time = time.time()

    try:
        # Execute git grep
        matches = git_grep(pattern, path, include, signal)

        # Sort matches
        try:
            # First try sorting by modification time
            stats = [os.stat(match) for match in matches]
            matches_with_stats = list(zip(matches, stats))
            matches_with_stats.sort(key=lambda x: x[1].st_mtime, reverse=True)
            matches = [match for match, _ in matches_with_stats]
        except Exception as e:
            # Fall back to sorting by name if there's an error
            logging.debug(f"Error sorting by modification time, falling back to name sort: {str(e)}")
            matches.sort()

        # Calculate execution time
        execution_time = int((time.time() - start_time) * 1000)  # Convert to milliseconds

        # Prepare output
        output = {
            "filenames": matches[:MAX_RESULTS],
            "durationMs": execution_time,
            "numFiles": len(matches),
        }

        return output
    except Exception as e:
        # Calculate execution time even on error
        execution_time = int((time.time() - start_time) * 1000)

        # Return empty results with error info
        return {
            "filenames": [],
            "durationMs": execution_time,
            "numFiles": 0,
            "error": str(e),
        }
