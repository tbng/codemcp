#!/usr/bin/env python3

import os
import logging
from typing import List, Tuple

from ..common import (
    MAX_LINE_LENGTH,
    MAX_LINES_TO_READ,
    MAX_OUTPUT_SIZE,
    normalize_file_path,
    find_git_root,
)
from ..rules import find_applicable_rules, Rule

__all__ = [
    "read_file_content",
]


async def read_file_content(
    file_path: str,
    offset: int | None = None,
    limit: int | None = None,
    chat_id: str | None = None,
) -> str:
    """Read a file's content with optional offset and limit.

    Args:
        file_path: The absolute path to the file to read
        offset: The line number to start reading from (1-indexed)
        limit: The number of lines to read
        chat_id: The unique ID of the current chat session

    Returns:
        The file content as a string, or an error message

    """
    try:
        # Normalize the file path
        full_file_path = normalize_file_path(file_path)

        # Validate the file path
        if not os.path.exists(full_file_path):
            # Try to find a similar file (stub - would need implementation)
            raise FileNotFoundError(f"File does not exist: {file_path}")

        if os.path.isdir(full_file_path):
            raise IsADirectoryError(f"Path is a directory, not a file: {file_path}")

        # Check file size before reading
        file_size = os.path.getsize(full_file_path)
        if file_size > MAX_OUTPUT_SIZE and not offset and not limit:
            raise ValueError(
                f"File content ({file_size // 1024}KB) exceeds maximum allowed size ({MAX_OUTPUT_SIZE // 1024}KB). Please use offset and limit parameters to read specific portions of the file."
            )

        # Handle text files - use async file operations with anyio
        from .async_file_utils import async_readlines

        all_lines = await async_readlines(
            full_file_path, encoding="utf-8", errors="replace"
        )

        # Get total line count
        total_lines = len(all_lines)

        # Handle offset (convert from 1-indexed to 0-indexed)
        line_offset = 0 if offset is None else (offset - 1 if offset > 0 else 0)

        # Apply offset and limit
        if line_offset >= total_lines:
            raise IndexError(
                f"Offset {offset} is beyond the end of the file (total lines: {total_lines})"
            )

        max_lines = MAX_LINES_TO_READ if limit is None else limit
        selected_lines = all_lines[line_offset : line_offset + max_lines]

        # Process lines (truncate long lines)
        processed_lines = []
        for line in selected_lines:
            if len(line) > MAX_LINE_LENGTH:
                processed_lines.append(
                    line[:MAX_LINE_LENGTH] + "... (line truncated)",
                )
            else:
                processed_lines.append(line)

        # Add line numbers (1-indexed)
        numbered_lines = []
        for i, line in enumerate(processed_lines):
            line_num = line_offset + i + 1  # 1-indexed line number
            numbered_lines.append(f"{line_num:6}\t{line.rstrip()}")

        content = "\n".join(numbered_lines)

        # Add a message if we truncated the file
        if line_offset + len(processed_lines) < total_lines:
            content += f"\n... (file truncated, showing {len(processed_lines)} of {total_lines} lines)"

        # Apply relevant cursor rules
        try:
            # Find git repository root
            repo_root = find_git_root(os.path.dirname(full_file_path))

            if repo_root:
                # Find applicable rules
                applicable_rules, suggested_rules = find_applicable_rules(
                    repo_root, full_file_path
                )

                # If we have applicable rules, add them to the output
                if applicable_rules or suggested_rules:
                    content += "\n\n// .cursor/rules results:"

                    # Add directly applicable rules
                    for rule in applicable_rules:
                        rule_content = f"\n\n// Rule from {os.path.relpath(rule.file_path, repo_root)}:\n{rule.payload}"
                        content += rule_content

                    # Add suggestions for rules with descriptions
                    for description, rule_path in suggested_rules:
                        rel_path = os.path.relpath(rule_path, repo_root)
                        content += f"\n\n// If {description} applies, load {rel_path}"
        except Exception as e:
            logging.warning(f"Error applying cursor rules: {e!s}", exc_info=True)
            # Don't fail the entire file read operation if rules can't be applied

        return content
    except Exception as e:
        return f"Error reading file: {e!s}"
