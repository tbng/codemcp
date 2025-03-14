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

    This function adds the codemcp-id to the end of a commit message with:
    - A double newline separator for single-line messages (even if they contain a colon)
    - A double newline separator for regular message content
    - A single newline separator if the line above is a metadata line of the form key: value

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

    # For single-line messages (subject only), always use double newline regardless of colon
    if len(lines) == 1:
        if message.endswith("\n"):
            return f"{message}\ncodemcp-id: {codemcp_id}"
        else:
            return f"{message}\n\ncodemcp-id: {codemcp_id}"
    # For multi-line messages, check if the last line looks like a metadata line (key: value)
    elif lines and ":" in lines[-1] and not lines[-1].startswith(" "):
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
    - Manages commit history entries in a consistent format
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
    # Remove any existing codemcp-id metadata
    main_message = re.sub(
        r"\ncodemcp-id:.*$", "", current_commit_message, flags=re.MULTILINE
    )

    # Remove any ```git-revs markdown blocks if they exist
    main_message = re.sub(r"```git-revs\n", "", main_message, flags=re.MULTILINE)
    main_message = re.sub(r"```\n", "", main_message, flags=re.MULTILINE)

    # Extract the original subject and body (everything before the revisions)
    # Split the message into lines to process
    lines = main_message.splitlines()

    # Collect revision entries and non-revision content separately
    rev_entries = []
    message_lines = []

    # Process each line
    in_revisions = False
    for line in lines:
        if "(Base revision)" in line:
            in_revisions = True
            rev_entries.append(line.strip())
        elif line.strip().startswith("HEAD") and in_revisions:
            # This is a HEAD entry in the revision section
            if commit_hash:
                # We're going to replace this with the actual commit hash
                head_pos = line.find("HEAD")
                head_len = len("HEAD")

                # Replace HEAD with commit hash
                line[:head_pos].strip()
                suffix = line[head_pos + head_len :].strip()

                # Add to revision entries, preserving alignment
                rev_entries.append(f"{commit_hash}  {suffix}")
            else:
                rev_entries.append(line.strip())
        elif in_revisions and line.strip() and not line.startswith("```"):
            # Other commit hash lines in the revision section
            rev_entries.append(line.strip())
        elif not in_revisions:
            # This is part of the main message
            message_lines.append(line)
        # Skip marker lines (```) and empty lines in the revision section

    # Clean up message lines (remove trailing empty lines)
    while message_lines and not message_lines[-1].strip():
        message_lines.pop()

    # Reconstruct the message part
    message_part = "\n".join(message_lines)

    # If we don't have a base revision marker but have a commit hash, add it
    has_base_revision = any("(Base revision)" in entry for entry in rev_entries)
    if not has_base_revision and commit_hash:
        rev_entries.insert(0, f"{commit_hash}  (Base revision)")

    # Add HEAD entry with the new description if provided
    if description:
        if commit_hash:
            # Use alignment to match the length of commit hash for consistent layout
            head_padding = " " * (len(commit_hash) - 4)  # 4 is length of "HEAD"
            rev_entries.append(f"HEAD{head_padding}  {description}")
        else:
            rev_entries.append(f"HEAD     {description}")

    # Build the final message
    formatted_rev_list = "\n".join(rev_entries)

    # We MUST NOT wrap the revision list in a markdown code block (```git-revs)
    # The test expects a plain format without markdown
    if message_part:
        if message_part.endswith("\n"):
            final_message = f"{message_part}\n{formatted_rev_list}"
        else:
            final_message = f"{message_part}\n\n{formatted_rev_list}"
    else:
        final_message = formatted_rev_list

    # Ensure the chat ID metadata is included if provided
    if chat_id:
        return append_metadata_to_message(final_message, {"codemcp-id": chat_id})
    else:
        return final_message
