#!/usr/bin/env python3

import logging
import os
import re
import subprocess
from typing import Dict, Tuple

from .common import normalize_file_path
from .shell import run_command

__all__ = [
    "is_git_repository",
    "commit_pending_changes",
    "commit_changes",
    "get_repository_root",
    "get_head_commit_chat_id",
    "get_head_commit_message",
    "get_head_commit_hash",
    "parse_git_commit_message",
    "append_metadata_to_message",
]

log = logging.getLogger(__name__)


async def get_head_commit_message(directory: str) -> str | None:
    """Get the full commit message from HEAD.

    Args:
        directory: The directory to check

    Returns:
        The commit message if available, None otherwise
    """
    try:
        # Check if HEAD exists
        result = await run_command(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=directory,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # No commits yet
            return None

        # Get the commit message
        result = await run_command(
            ["git", "log", "-1", "--pretty=%B"],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()
    except Exception as e:
        logging.warning(
            f"Exception when getting HEAD commit message: {e!s}", exc_info=True
        )
        return None


def parse_git_commit_message(message: str) -> Tuple[str, Dict[str, str]]:
    """Parse a Git commit message into main message and metadata.

    This function handles Git commit message trailer/footer sections according to Git conventions.
    Metadata (trailers) are key-value pairs at the end of the commit message, separated from
    the main message by a blank line. Each trailer is on its own line and follows the format
    "Key: Value".

    Args:
        message: The full Git commit message

    Returns:
        A tuple containing (main_message, metadata_dict)
        - main_message: The main commit message without the trailer metadata
        - metadata_dict: A dictionary of metadata key-value pairs
    """
    if not message:
        return "", {}

    # Special case for single-line messages with no metadata
    if "\n" not in message:
        return message, {}

    # Check if message ends with "Key: Value" pattern that is common in metadata
    # If not, we can quickly return the whole message
    lines = message.splitlines()
    last_line = lines[-1].strip() if lines else ""
    if not re.match(
        r"^([A-Za-z0-9][A-Za-z0-9_.-]*(?:-[A-Za-z0-9_.-]+)*):\s*(.*)$", last_line
    ):
        return message, {}

    # Split message into blocks by blank lines
    blocks = []
    current_block = []

    for line in lines:
        if not line.strip():
            if current_block:
                blocks.append(current_block)
                current_block = []
        else:
            current_block.append(line)

    if current_block:
        blocks.append(current_block)

    # No blocks means no content
    if not blocks:
        return "", {}

    # Check if the last block consists entirely of "Key: Value" format lines
    last_block = blocks[-1]

    # Detect if the last block is a valid metadata section
    is_metadata_section = True
    parsed_metadata = {}
    current_key = None
    current_values = []

    for i, line in enumerate(last_block):
        # Check if line matches Key: Value format with support for hyphenated keys
        # Git allows various formats like "Signed-off-by:", "Co-authored-by:", etc.
        kvp_match = re.match(
            r"^([A-Za-z0-9][A-Za-z0-9_.-]*(?:-[A-Za-z0-9_.-]+)*):\s*(.*)$", line
        )

        if kvp_match:
            # Found a new key-value pair
            if current_key:
                # Save the previous key-value pair
                parsed_metadata[current_key] = "\n".join(current_values)

            current_key = kvp_match.group(1)
            current_values = [kvp_match.group(2)]
        elif line.startswith(" ") and current_key:
            # Continuation line (indented)
            current_values.append(line)
        else:
            # Not a valid trailer format
            is_metadata_section = False
            break

    # Save the last key-value pair if there was one
    if current_key and is_metadata_section:
        parsed_metadata[current_key] = "\n".join(current_values)

    # If the entire last block consists of valid metadata, use it
    if is_metadata_section and parsed_metadata:
        # Return main message (all blocks except the last)
        if len(blocks) > 1:
            # Reconstruct the main message preserving blank lines
            main_parts = []
            for i, block in enumerate(blocks[:-1]):
                main_parts.append("\n".join(block))

            main_message = "\n\n".join(main_parts)
            return main_message, parsed_metadata
        else:
            # If only metadata block exists, main message is empty
            return "", parsed_metadata

    # If we get here, there is no valid metadata section
    # Return the full message as main message
    return message, {}


def append_metadata_to_message(message: str, metadata: Dict[str, str]) -> str:
    """Append or update metadata to a Git commit message.

    Args:
        message: The original Git commit message
        metadata: Dictionary of metadata key-value pairs to append/update

    Returns:
        The updated commit message with metadata appended or updated
    """
    if not metadata:
        return message

    # Parse the original message to extract existing content and metadata
    main_message, existing_metadata = parse_git_commit_message(message)

    # Update existing metadata with new values
    updated_metadata = {**existing_metadata, **metadata}

    # Reconstruct the message with main content and updated metadata
    result = main_message

    if updated_metadata:
        # Add a blank line separator if needed
        if main_message and not main_message.endswith("\n\n"):
            if not main_message.endswith("\n"):
                result += "\n"
            result += "\n"

        # Add each metadata entry in a consistent order
        # Sort keys but put codemcp-id at the end (conventional for Git trailers)
        sorted_keys = sorted(updated_metadata.keys())
        if "codemcp-id" in sorted_keys:
            sorted_keys.remove("codemcp-id")
            sorted_keys.append("codemcp-id")

        for key in sorted_keys:
            result += f"{key}: {updated_metadata[key]}\n"

    return result.rstrip()


async def get_head_commit_hash(directory: str, short: bool = True) -> str | None:
    """Get the commit hash from HEAD.

    Args:
        directory: The directory to check
        short: Whether to get short hash (default) or full hash

    Returns:
        The commit hash if available, None otherwise
    """
    try:
        # Check if HEAD exists
        result = await run_command(
            ["git", "rev-parse", "--verify", "HEAD"],
            cwd=directory,
            check=False,
            capture_output=True,
            text=True,
        )

        if result.returncode != 0:
            # No commits yet
            return None

        # Get the commit hash (short or full)
        cmd = ["git", "rev-parse"]
        if short:
            cmd.append("--short")
        cmd.append("HEAD")

        result = await run_command(
            cmd,
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()
    except Exception as e:
        logging.warning(
            f"Exception when getting HEAD commit hash: {e!s}", exc_info=True
        )
        return None


async def get_head_commit_chat_id(directory: str) -> str | None:
    """Get the chat ID from the HEAD commit's message.

    Args:
        directory: The directory to check

    Returns:
        The chat ID if found, None otherwise
    """
    try:
        commit_message = await get_head_commit_message(directory)
        if not commit_message:
            return None

        # Parse the commit message and extract metadata
        _, metadata = parse_git_commit_message(commit_message)

        # Return the chat ID if present in metadata
        return metadata.get("codemcp-id")
    except Exception as e:
        logging.warning(
            f"Exception when getting HEAD commit chat ID: {e!s}", exc_info=True
        )
        return None


async def get_repository_root(path: str) -> str:
    """Get the root directory of the Git repository containing the path.

    Args:
        path: The file path to get the repository root for

    Returns:
        The absolute path to the repository root

    Raises:
        ValueError: If the path is not in a Git repository
    """
    try:
        # Get the directory containing the file or use the path itself if it's a directory
        directory = os.path.dirname(path) if os.path.isfile(path) else path

        # Get the absolute path to ensure consistency
        directory = os.path.abspath(directory)

        # Get the repository root
        result = await run_command(
            ["git", "rev-parse", "--show-toplevel"],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        return result.stdout.strip()
    except (subprocess.SubprocessError, OSError) as e:
        raise ValueError(f"Path is not in a git repository: {str(e)}")


async def is_git_repository(path: str) -> bool:
    """Check if the path is within a Git repository.

    Args:
        path: The file path to check

    Returns:
        True if path is in a Git repository, False otherwise

    """
    try:
        # Get the directory containing the file or use the path itself if it's a directory
        directory = os.path.dirname(path) if os.path.isfile(path) else path

        # Get the absolute path to ensure consistency
        directory = os.path.abspath(directory)

        # Run git command to verify this is a git repository
        await run_command(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=directory,
            check=True,
            capture_output=True,
            text=True,
        )

        # Also get the repository root to use for all git operations
        try:
            await run_command(
                ["git", "rev-parse", "--show-toplevel"],
                cwd=directory,
                check=True,
                capture_output=True,
                text=True,
            )

            # Store the repository root in a global or class variable if needed
            # This could be used to ensure all git operations use the same root

            return True
        except (subprocess.SubprocessError, OSError):
            # If we can't get the repo root, it's not a proper git repository
            return False
    except (subprocess.SubprocessError, OSError):
        return False


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
                # Parse the message into lines
                lines = main_message.splitlines()

                # Check if we need to add a base revision marker
                has_base_revision = any("(Base revision)" in line for line in lines)

                if not has_base_revision:
                    # First commit with this chat_id, mark it as base revision
                    if lines and lines[-1].strip():
                        # Previous line has content, add two newlines
                        main_message += f"\n\n{commit_hash}  (Base revision)"
                    else:
                        # Previous line is blank, just add one newline
                        main_message += f"\n{commit_hash}  (Base revision)"

                # Define a consistent padding for alignment - ensure hash and HEAD are aligned
                hash_len = len(commit_hash)  # Typically 7 characters
                head_padding = " " * (hash_len - 4)  # 4 is the length of "HEAD"

                # Update any existing HEAD entries to have actual hashes
                new_lines = []
                for line in main_message.splitlines():
                    if line.strip().startswith("HEAD"):
                        # Calculate alignment adjustment since HEAD is shorter than commit hash (typically 7 chars)
                        # Find HEAD in the line and replace it while preserving alignment
                        # This will ensure descriptions remain aligned after replacement
                        head_pos = line.find("HEAD")
                        head_len = len("HEAD")
                        hash_len = len(commit_hash)

                        # Calculate the difference in length between HEAD and the hash
                        len_diff = hash_len - head_len

                        # Replace HEAD with the commit hash and adjust spaces to maintain alignment
                        prefix = line[:head_pos]
                        suffix = line[head_pos + head_len :]
                        # Remove leading spaces from suffix equal to the length difference
                        if len_diff > 0 and suffix.startswith(" " * len_diff):
                            suffix = suffix[len_diff:]
                        new_line = prefix + commit_hash + suffix
                        new_lines.append(new_line)
                    else:
                        new_lines.append(line)

                # Reconstruct the message with updated lines
                main_message = "\n".join(new_lines)

                # Now add the new entry with HEAD, ensuring alignment with hash entries
                # We need precise spacing to match with the formatting in the commit message
                main_message += f"\nHEAD{head_padding}  {description}"
            else:
                main_message = description
                # Add base revision marker for the first commit
                main_message += f"\n\n{commit_hash}  (Base revision)"

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
