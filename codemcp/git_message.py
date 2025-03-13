#!/usr/bin/env python3

import logging
import re

__all__ = [
    "append_metadata_to_message",
    "update_commit_message_with_description",
]

log = logging.getLogger(__name__)


def append_metadata_to_message(message: str, metadata: dict) -> str:
    """Append codemcp-id to a Git commit message.

    This function adds the codemcp-id to the end of a commit message with a double newline
    separator unless the line above is a metadata line of the form key: value.

    Args:
        message: The original Git commit message
        metadata: Dictionary containing metadata; only codemcp-id is used

    Returns:
        The updated commit message with codemcp-id appended
    """
    if not metadata or "codemcp-id" not in metadata:
        return message

    codemcp_id = metadata["codemcp-id"]

    # If the message is empty, just return the codemcp-id
    if not message:
        return f"codemcp-id: {codemcp_id}"

    # Split the message into lines to analyze the last line
    lines = message.splitlines()

    # Check if the last line looks like a metadata line (key: value)
    if lines and ":" in lines[-1] and not lines[-1].startswith(" "):
        # If the last line looks like metadata, append without double newline
        if message.endswith("\n"):
            return f"{message}codemcp-id: {codemcp_id}"
        else:
            return f"{message}\ncodemcp-id: {codemcp_id}"
    else:
        # Otherwise, append with double newline
        if message.endswith("\n\n"):
            return f"{message}codemcp-id: {codemcp_id}"
        elif message.endswith("\n"):
            return f"{message}\ncodemcp-id: {codemcp_id}"
        else:
            return f"{message}\n\ncodemcp-id: {codemcp_id}"


def update_commit_message_with_description(
    current_commit_message: str,
    description: str,
    commit_hash: str = None,
    chat_id: str = None,
) -> str:
    """Update a commit message with a new description.

    This function handles the message munging logic for commit messages:
    - Updates the message by adding the description as a new entry
    - Handles base revision markers and HEAD alignment
    - Ensures the chat_id metadata is included

    Args:
        current_commit_message: The current Git commit message to update
        description: The new description to add to the message
        commit_hash: The current commit hash (used for updating HEAD entries and base revision)
        chat_id: The chat ID to ensure is in the metadata

    Returns:
        The updated commit message with the new description
    """
    # Extract the commit message without any codemcp-id
    main_message = re.sub(
        r"\ncodemcp-id:.*$", "", current_commit_message, flags=re.MULTILINE
    )

    if main_message:
        # Parse the message into lines
        lines = main_message.splitlines()

        # Check if we need to add a base revision marker
        has_base_revision = any("(Base revision)" in line for line in lines)

        if not has_base_revision and commit_hash:
            # First commit with this chat_id, mark it as base revision
            if lines and lines[-1].strip():
                # Previous line has content, add two newlines
                main_message += f"\n\n{commit_hash}  (Base revision)"
            else:
                # Previous line is blank, just add one newline
                main_message += f"\n{commit_hash}  (Base revision)"

        if commit_hash:
            # Define a consistent padding for alignment - ensure hash and HEAD are aligned
            hash_len = len(commit_hash)  # Typically 7 characters
            head_padding = " " * (hash_len - 4)  # 4 is the length of "HEAD"

            # Update any existing HEAD entries to have actual hashes
            new_lines = []
            for line in lines:
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
            if description:  # Only add HEAD line if there's a description to add
                main_message += f"\nHEAD{head_padding}  {description}"
        else:
            # No commit hash, just append the description
            if description:  # Only append if there's a description to add
                if main_message and not main_message.endswith("\n"):
                    main_message += "\n"
                main_message += description
    else:
        # No existing main message, just use the description
        main_message = description

        # Add base revision marker for the first commit if we have a commit hash
        if commit_hash and description:
            main_message += f"\n\n{commit_hash}  (Base revision)"

    # Ensure the chat ID metadata is included if provided
    if chat_id:
        return append_metadata_to_message(main_message, {"codemcp-id": chat_id})
    else:
        return main_message
