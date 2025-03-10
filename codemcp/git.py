#!/usr/bin/env python3

import logging
import os
import subprocess
from typing import Tuple

from .common import normalize_file_path


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
        result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=True,
            text=True,
        )
        # Log command output instead of sending to stdout
        if result.stdout:
            logging.debug("git rev-parse output: %s", result.stdout.strip())
        if result.stderr:
            logging.debug("git rev-parse stderr: %s", result.stderr.strip())
        return True
    except (subprocess.SubprocessError, OSError):
        return False


def commit_pending_changes(file_path: str) -> Tuple[bool, str]:
    """Commit any pending changes in the repository, excluding the target file.

    Args:
        file_path: The path to the file to exclude from committing

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

        # Log command output
        if file_status.stdout:
            logging.debug("git ls-files output: %s", file_status.stdout.strip())
        if file_status.stderr:
            logging.debug("git ls-files stderr: %s", file_status.stderr.strip())

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

        # Log command output
        if status_result.stdout:
            logging.debug("git status output: %s", status_result.stdout.strip())
        if status_result.stderr:
            logging.debug("git status stderr: %s", status_result.stderr.strip())

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
                add_result = subprocess.run(
                    ["git", "add", "."],
                    cwd=directory,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Log command output
                if add_result.stdout:
                    logging.debug("git add output: %s", add_result.stdout.strip())
                if add_result.stderr:
                    logging.debug("git add stderr: %s", add_result.stderr.strip())

                commit_snapshot_result = subprocess.run(
                    ["git", "commit", "-m", "Snapshot before codemcp change"],
                    cwd=directory,
                    check=True,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True
                )

                # Log command output
                if commit_snapshot_result.stdout:
                    logging.debug("git commit snapshot output: %s", commit_snapshot_result.stdout.strip())
                if commit_snapshot_result.stderr:
                    logging.debug("git commit snapshot stderr: %s", commit_snapshot_result.stderr.strip())

                return True, "Committed pending changes"

        return True, "No pending changes to commit"
    except Exception as e:
        return False, f"Error committing pending changes: {str(e)}"


def commit_changes(file_path: str, description: str) -> Tuple[bool, str]:
    """Commit changes to a file in Git.

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

        # Add the specified file
        add_result = subprocess.run(
            ["git", "add", file_path],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Log command output
        if add_result.stdout:
            logging.debug("git add file output: %s", add_result.stdout.strip())
        if add_result.stderr:
            logging.debug("git add file stderr: %s", add_result.stderr.strip())

        if add_result.returncode != 0:
            return False, f"Failed to add file to Git: {add_result.stderr}"

        # First check if there's already a commit in the repository
        has_commits = False
        rev_parse_result = subprocess.run(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=directory,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        # Log command output
        if rev_parse_result.stdout:
            logging.debug("git rev-parse HEAD output: %s", rev_parse_result.stdout.strip())
        if rev_parse_result.stderr:
            logging.debug("git rev-parse HEAD stderr: %s", rev_parse_result.stderr.strip())

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
                text=True,
            )

            # Log command output (only stderr since stdout would be empty with --quiet flag)
            if diff_result.stderr:
                logging.debug("git diff-index stderr: %s", diff_result.stderr.strip())

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

        # Log command output
        if commit_result.stdout:
            logging.debug("git commit output: %s", commit_result.stdout.strip())
        if commit_result.stderr:
            logging.debug("git commit stderr: %s", commit_result.stderr.strip())

        if commit_result.returncode != 0:
            return False, f"Failed to commit changes: {commit_result.stderr}"

        return True, "Changes committed successfully"
    except Exception as e:
        return False, f"Error committing changes: {str(e)}"
