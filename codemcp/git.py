#!/usr/bin/env python3

"""Git operations and utilities.

This module provides Git-related functionality for the codemcp tool.
The actual implementation is split across several modules:
- git_core.py: Basic Git operations and repository checks
- git_commit.py: Functions related to creating and modifying commits
- git_message.py: Functions for parsing and formatting Git commit messages
"""

# Re-export all functionality from the specialized modules
from .git_commit import (
    commit_changes,
    commit_pending_changes,
    create_commit_reference,
)
from .git_core import (
    get_head_commit_chat_id,
    get_head_commit_hash,
    get_head_commit_message,
    get_ref_commit_chat_id,
    get_repository_root,
    is_git_repository,
)
from .git_message import (
    append_metadata_to_message,
    format_commit_message_with_git_revs,
    parse_git_commit_message,
)

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
    "create_commit_reference",
    "get_ref_commit_chat_id",
    "format_commit_message_with_git_revs",
]
