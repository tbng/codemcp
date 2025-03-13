#!/usr/bin/env python3

import logging
import os
import subprocess

from .common import normalize_file_path
from .git_core import (
    get_head_commit_chat_id,
    get_head_commit_hash,
    get_head_commit_message,
    is_git_repository,
)
from .git_message import (
    append_metadata_to_message,
    format_commit_message_with_git_revs,
    parse_git_commit_message,
)
from .shell import run_command

__all__ = [
    "commit_pending_changes",
    "commit_changes",
    "create_commit_reference",
]

log = logging.getLogger(__name__)


async def commit_pending_changes(file_path: str) -> tuple[bool, str]:
    """Commit any pending changes in the repository, excluding the target file.

    Args:
        file_path: The path to the file to exclude from committing

    Returns:
        A tuple of (success, message)

    """
    try:
        # First, check if this is a git repository
        if not await is_git_repository(file_path):
            return False, "File is not in a Git repository"

        directory = os.path.dirname(file_path)

        # Check if the file is tracked by git
        file_status = await run_command(
            ["git", "ls-files", "--error-unmatch", file_path],
            cwd=directory,
            capture_output=True,
            text=True,
            check=False,
        )

        file_is_tracked = file_status.returncode == 0

        # If the file is not tracked, return an error
        if not file_is_tracked:
            return (
                False,
                "File is not tracked by git. Please add the file to git tracking first using 'git add <file>'",
            )

        # Check if working directory has uncommitted changes
        status_result = await run_command(
            ["git", "status", "--porcelain"],
            cwd=directory,
            capture_output=True,
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
                await run_command(
                    ["git", "add", "."],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                await run_command(
                    ["git", "commit", "-m", "unknown: Snapshot before codemcp change"],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                    text=True,
                )

                return True, "Committed pending changes"

        return True, "No pending changes to commit"
    except Exception as e:
        logging.warning(
            f"Exception suppressed when committing pending changes: {e!s}",
            exc_info=True,
        )
        return False, f"Error committing pending changes: {e!s}"


async def create_commit_reference(
    path: str,
    description: str,
    chat_id: str,
    ref_name: str = None,
    custom_message: str = None,
) -> tuple[bool, str, str]:
    """Create a Git commit without advancing HEAD and store it in a reference.

    This function creates a commit using Git plumbing commands and stores it in
    a reference (refs/codemcp/<chat_id>) without changing HEAD.

    Args:
        path: The path to the file or directory to commit
        description: Commit message describing the change
        chat_id: The unique ID of the current chat session
        ref_name: Optional custom reference name (defaults to refs/codemcp/<chat_id>)
        custom_message: Optional custom commit message (overrides description)

    Returns:
        A tuple of (success, message, commit_hash)
    """
    log.debug(
        "create_commit_reference(%s, %s, %s, %s)", path, description, chat_id, ref_name
    )
    try:
        # First, check if this is a git repository
        if not await is_git_repository(path):
            return False, f"Path '{path}' is not in a Git repository", ""

        # Get absolute paths for consistency
        abs_path = os.path.abspath(path)

        # Get the directory - if path is a file, use its directory, otherwise use the path itself
        directory = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path

        # Try to get the git repository root for more reliable operations
        try:
            repo_root = (
                await run_command(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            ).stdout.strip()

            # Use the repo root as the working directory for git commands
            git_cwd = repo_root
        except (subprocess.SubprocessError, OSError):
            # Fall back to the directory if we can't get the repo root
            git_cwd = directory

        # Use the default reference name if none provided
        if ref_name is None:
            ref_name = f"refs/codemcp/{chat_id}"

        # Create the tree object for the empty commit
        # Get the tree from HEAD or create a new empty tree if no HEAD exists
        tree_hash = ""
        has_commits = False
        rev_parse_result = await run_command(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        if rev_parse_result.returncode == 0:
            has_commits = True
            tree_result = await run_command(
                ["git", "show", "-s", "--format=%T", "HEAD"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            tree_hash = tree_result.stdout.strip()
        else:
            # Create an empty tree if no HEAD exists
            empty_tree_result = await run_command(
                ["git", "mktree"],
                cwd=git_cwd,
                input="",
                capture_output=True,
                text=True,
                check=True,
            )
            tree_hash = empty_tree_result.stdout.strip()

        # Prepare the commit message with metadata
        if custom_message:
            # Parse the custom message to extract main content and metadata
            main_message, metadata_dict = parse_git_commit_message(custom_message)

            # Make sure it has the chat_id metadata
            if chat_id:
                metadata_dict["codemcp-id"] = chat_id

            # Reconstruct the message with metadata
            commit_message = append_metadata_to_message(main_message, metadata_dict)
        else:
            commit_message = description
            if chat_id:
                commit_message = append_metadata_to_message(
                    commit_message, {"codemcp-id": chat_id}
                )

        # Get parent commit if we have HEAD
        parent_arg = []
        if has_commits:
            head_hash_result = await run_command(
                ["git", "rev-parse", "HEAD"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=True,
            )
            head_hash = head_hash_result.stdout.strip()
            parent_arg = ["-p", head_hash]

        # Create the commit object
        commit_result = await run_command(
            ["git", "commit-tree", tree_hash, *parent_arg, "-m", commit_message],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=True,
        )
        commit_hash = commit_result.stdout.strip()

        # Update the reference to point to the new commit
        await run_command(
            ["git", "update-ref", ref_name, commit_hash],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=True,
        )

        return (
            True,
            f"Created commit reference {ref_name} -> {commit_hash}",
            commit_hash,
        )
    except Exception as e:
        logging.warning(
            f"Exception when creating commit reference: {e!s}", exc_info=True
        )
        return False, f"Error creating commit reference: {e!s}", ""


async def commit_changes(
    path: str,
    description: str,
    chat_id: str = None,
    allow_empty: bool = False,
    custom_message: str = None,
) -> tuple[bool, str]:
    """Commit changes to a file or directory in Git.

    This function will either create a new commit with the chat_id metadata,
    or amend the HEAD commit if it belongs to the same chat session.

    If HEAD doesn't have the right chat_id but there's a commit reference for this
    chat_id, it will cherry-pick that reference first to create the initial commit
    and then proceed with the changes.

    Args:
        path: The path to the file or directory to commit
        description: Commit message describing the change
        chat_id: The unique ID of the current chat session
        allow_empty: Whether to allow empty commits (no changes)
        custom_message: Optional custom commit message (overrides description)

    Returns:
        A tuple of (success, message)

    """
    log.debug("commit_changes(%s, %s, %s)", path, description, chat_id)
    try:
        # First, check if this is a git repository
        if not await is_git_repository(path):
            return False, f"Path '{path}' is not in a Git repository"

        # Get absolute paths for consistency
        abs_path = os.path.abspath(path)

        # Get the directory - if path is a file, use its directory, otherwise use the path itself
        directory = os.path.dirname(abs_path) if os.path.isfile(abs_path) else abs_path

        # Try to get the git repository root for more reliable operations
        try:
            repo_root = (
                await run_command(
                    ["git", "rev-parse", "--show-toplevel"],
                    cwd=directory,
                    check=True,
                    capture_output=True,
                    text=True,
                )
            ).stdout.strip()

            # Use the repo root as the working directory for git commands
            git_cwd = repo_root
        except (subprocess.SubprocessError, OSError):
            # Fall back to the directory if we can't get the repo root
            git_cwd = directory

        # If it's a file, check if it exists
        if os.path.isfile(abs_path) and not os.path.exists(abs_path):
            return False, f"File does not exist: {abs_path}"

        # Add the path to git - could be a file or directory
        try:
            # If path is a directory, do git add .
            add_command = (
                ["git", "add", "."]
                if os.path.isdir(abs_path)
                else ["git", "add", abs_path]
            )

            add_result = await run_command(
                add_command,
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        except Exception as e:
            return False, f"Failed to add to Git: {str(e)}"

        if add_result.returncode != 0:
            return False, f"Failed to add to Git: {add_result.stderr}"

        # First check if there's already a commit in the repository
        has_commits = False
        rev_parse_result = await run_command(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=git_cwd,
            capture_output=True,
            text=True,
            check=False,
        )

        has_commits = rev_parse_result.returncode == 0

        # Check if there are any staged changes to commit
        if has_commits:
            # Check if there are any changes to commit after git add
            diff_result = await run_command(
                ["git", "diff-index", "--cached", "--quiet", "HEAD"],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )

            # If diff-index returns 0, there are no changes to commit
            if diff_result.returncode == 0 and not allow_empty:
                return (
                    True,
                    "No changes to commit (changes already committed or no changes detected)",
                )

        # Determine whether to amend or create a new commit
        head_chat_id = await get_head_commit_chat_id(git_cwd) if has_commits else None
        logging.debug(
            "commit_changes: has_commits = %r, head_chat_id = %s",
            has_commits,
            head_chat_id,
        )

        # If HEAD exists but doesn't have the right chat_id, check if we have a
        # commit reference for this chat_id that we need to cherry-pick first
        if has_commits and chat_id and head_chat_id != chat_id:
            ref_name = f"refs/codemcp/{chat_id}"
            ref_exists = False

            # Check if the reference exists
            ref_result = await run_command(
                ["git", "show-ref", "--verify", ref_name],
                cwd=git_cwd,
                check=False,
                capture_output=True,
                text=True,
            )
            ref_exists = ref_result.returncode == 0

            if ref_exists:
                # Using git plumbing commands instead of cherry-pick to avoid conflicts with local changes
                logging.info(f"Creating a new commit from reference {ref_name}")

                # Get the current HEAD commit hash
                head_hash = await get_head_commit_hash(git_cwd, short=False)

                # Get the tree from HEAD
                tree_result = await run_command(
                    ["git", "show", "-s", "--format=%T", "HEAD"],
                    cwd=git_cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                tree_hash = tree_result.stdout.strip()

                # Get the commit message from the reference
                ref_message_result = await run_command(
                    ["git", "log", "-1", "--pretty=%B", ref_name],
                    cwd=git_cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                ref_message = ref_message_result.stdout.strip()

                # Create a new commit with the same tree as HEAD but message from the reference
                # This effectively creates the commit without changing the working tree
                new_commit_result = await run_command(
                    [
                        "git",
                        "commit-tree",
                        tree_hash,
                        "-p",
                        head_hash,
                        "-m",
                        ref_message,
                    ],
                    cwd=git_cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )
                new_commit_hash = new_commit_result.stdout.strip()

                # Update HEAD to point to the new commit
                await run_command(
                    ["git", "update-ref", "HEAD", new_commit_hash],
                    cwd=git_cwd,
                    capture_output=True,
                    text=True,
                    check=True,
                )

                logging.info(
                    f"Successfully applied reference commit for chat ID {chat_id}"
                )
                # After applying, the HEAD commit should have the right chat_id
                head_chat_id = await get_head_commit_chat_id(git_cwd)

        should_amend = has_commits and head_chat_id == chat_id

        # Prepare the commit message with metadata
        if custom_message:
            # Parse the custom message to extract main content and metadata
            main_message, metadata_dict = parse_git_commit_message(custom_message)

            # Make sure it has the chat_id metadata
            if chat_id:
                metadata_dict["codemcp-id"] = chat_id

            # Reconstruct the message with metadata
            commit_message = append_metadata_to_message(main_message, metadata_dict)
        else:
            commit_message = f"wip: {description}"

        if should_amend:
            # Get the current commit hash before amending
            commit_hash = await get_head_commit_hash(git_cwd)

            # Get the current commit message
            current_commit_message = await get_head_commit_message(git_cwd)
            if not current_commit_message:
                current_commit_message = ""

            # Parse the commit message to extract main content and metadata
            main_message, metadata_dict = parse_git_commit_message(
                current_commit_message
            )

            # Verify the commit has our codemcp-id
            if chat_id and "codemcp-id" not in metadata_dict:
                logging.warning("Expected codemcp-id in current commit but not found")

            # Add the new description to the message body
            if main_message:
                # Call the helper function to update the message with the git-revs block
                main_message = format_commit_message_with_git_revs(
                    main_message, commit_hash, description
                )
            else:
                # For the very first commit, create a simple message with git-revs block
                main_message = format_commit_message_with_git_revs(
                    "", commit_hash, description
                )

            # Ensure the chat ID metadata is included
            metadata_dict["codemcp-id"] = chat_id

            # Reconstruct the message with updated metadata
            commit_message = append_metadata_to_message(main_message, metadata_dict)

            # Amend the previous commit
            commit_result = await run_command(
                ["git", "commit", "--amend", "-m", commit_message],
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )
        else:
            # For new commits, ensure chat ID is added to the message
            if chat_id:
                # Parse the message and add metadata
                main_message, metadata_dict = parse_git_commit_message(commit_message)
                metadata_dict["codemcp-id"] = chat_id
                commit_message = append_metadata_to_message(main_message, metadata_dict)

            # Create a new commit
            commit_cmd = ["git", "commit", "-m", commit_message]
            if allow_empty:
                commit_cmd.append("--allow-empty")

            commit_result = await run_command(
                commit_cmd,
                cwd=git_cwd,
                capture_output=True,
                text=True,
                check=False,
            )

        if commit_result.returncode != 0:
            return False, f"Failed to commit changes: {commit_result.stderr}"

        # Get the new commit hash
        await get_head_commit_hash(git_cwd)

        verb = "amended" if should_amend else "committed"

        # If this was an amended commit, include the original hash in the message
        if should_amend and commit_hash:
            return (
                True,
                f"Changes {verb} successfully (previous commit was {commit_hash})",
            )
        else:
            return True, f"Changes {verb} successfully"
    except Exception as e:
        logging.warning(
            f"Exception suppressed when committing changes: {e!s}", exc_info=True
        )
        return False, f"Error committing changes: {e!s}"
