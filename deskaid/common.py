#!/usr/bin/env python3

import logging
import mimetypes
import os
import subprocess
from typing import List, Optional, Tuple

# Constants
MAX_LINES_TO_READ = 1000
MAX_LINE_LENGTH = 1000
MAX_OUTPUT_SIZE = 0.25 * 1024 * 1024  # 0.25MB in bytes


def is_image_file(file_path: str) -> bool:
    """Check if a file is an image based on its MIME type."""
    # Stub implementation - we don't care about image support
    return False


def get_image_format(file_path: str) -> str:
    """Get the format of an image file."""
    # Stub implementation - we don't care about image support
    return "png"


def normalize_file_path(file_path: str) -> str:
    """Normalize a file path to an absolute path."""
    if not os.path.isabs(file_path):
        return os.path.abspath(os.path.join(os.getcwd(), file_path))
    return os.path.abspath(file_path)


def is_git_repository(path: str) -> bool:
    """Check if the path is within a Git repository.

    Args:
        path: The file path to check

    Returns:
        True if path is in a Git repository, False otherwise
    """
    try:
        # Get the directory containing the file
        directory = os.path.dirname(path) if os.path.isfile(path) else path

        # Run git command to verify this is a git repository
        subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def commit_changes(file_path: str, description: str) -> Tuple[bool, str]:
    """Commit changes to a file in Git.

    If the working directory has uncomitted changes, will commit those first
    with a default message before making the requested commit.

    Args:
        file_path: The path to the file to commit
        description: Commit message describing the change

    Returns:
        A tuple of (success, message)
    """
    try:
        # First, check if this is a git repository
        if not is_git_repository(file_path):
            return False, "File is not in a Git repository"

        directory = os.path.dirname(file_path)

        # Check if the file is tracked by git
        file_status = subprocess.run(
            ["git", "ls-files", "--error-unmatch", file_path],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        file_is_tracked = file_status.returncode == 0

        # Check if working directory has uncommitted changes
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )

        # If there are uncommitted changes (besides our target file), commit them first
        if status_result.stdout and file_is_tracked:
            # Get list of changed files
            changed_files = []
            for line in status_result.stdout.splitlines():
                # Skip empty lines
                if not line.strip():
                    continue
                    
                # git status --porcelain output format: XY filename
                # where X is status in staging area, Y is status in working tree
                # There are at least 2 spaces before the filename
                parts = line.strip().split(" ", 1)
                if len(parts) > 1:
                    # Extract the filename, removing any leading spaces
                    filename = parts[1].lstrip()
                    full_path = normalize_file_path(os.path.join(directory, filename))
                    # Skip our target file
                    if full_path != normalize_file_path(file_path):
                        changed_files.append(filename)

            if changed_files:
                # Commit other changes first with a default message
                subprocess.run(["git", "add", "."], cwd=directory, check=True)

                subprocess.run(
                    ["git", "commit", "-m", "Snapshot before deskaid change"],
                    cwd=directory,
                    check=True,
                )

        # Add the specified file
        add_result = subprocess.run(
            ["git", "add", file_path],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if add_result.returncode != 0:
            return False, f"Failed to add file to Git: {add_result.stderr}"
            
        # First check if there's already a commit in the repository
        has_commits = False
        rev_parse_result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        has_commits = rev_parse_result.returncode == 0
        
        # Only check for changes if we already have commits
        if has_commits:
            # Check if there are any changes to commit after git add
            # Using git diff-index HEAD to check for staged changes against HEAD
            diff_result = subprocess.run(
                ["git", "diff-index", "--cached", "--quiet", "HEAD", "--", file_path],
                cwd=directory,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
            
            # If diff-index returns 0, there are no changes to commit for this file
            if diff_result.returncode == 0:
                return True, "No changes to commit (file is identical to what's already committed)"

        # Commit the change
        commit_result = subprocess.run(
            ["git", "commit", "-m", description],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        if commit_result.returncode != 0:
            return False, f"Failed to commit changes: {commit_result.stderr}"

        return True, "Changes committed successfully"
    except Exception as e:
        return False, f"Error committing changes: {str(e)}"


def get_edit_snippet(
    original_text: str, old_str: str, new_str: str, context_lines: int = 4
) -> str:
    """
    Generate a snippet of the edited file showing the changes with line numbers.

    Args:
        original_text: The original file content
        old_str: The text that was replaced
        new_str: The new text that replaced old_str
        context_lines: Number of lines to show before and after the change

    Returns:
        A formatted string with line numbers and the edited content
    """
    # Find where the edit occurs
    before_text = original_text.split(old_str)[0]
    before_lines = before_text.split("\n")
    replacement_line = len(before_lines)

    # Get the edited content
    edited_text = original_text.replace(old_str, new_str)
    edited_lines = edited_text.split("\n")

    # Calculate the start and end line numbers for the snippet
    start_line = max(0, replacement_line - context_lines)
    end_line = min(
        len(edited_lines), replacement_line + context_lines + len(new_str.split("\n"))
    )

    # Extract the snippet lines
    snippet_lines = edited_lines[start_line:end_line]

    # Format with line numbers
    result = []
    for i, line in enumerate(snippet_lines):
        line_num = start_line + i + 1
        result.append(f"{line_num:4d} | {line}")

    return "\n".join(result)
