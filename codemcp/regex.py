#!/usr/bin/env python3

"""Centralized regular expression patterns for codemcp."""

# Regular expression for valid chat ID format (a-zA-Z0-9-)
CHAT_ID_REGEX = r"[a-zA-Z0-9-]+"

# Regular expression for validating a complete chat ID (must be all a-zA-Z0-9- characters)
CHAT_ID_VALIDATION_REGEX = f"^{CHAT_ID_REGEX}$"

# Regular expression for extracting chat ID from commit message
COMMIT_CHAT_ID_REGEX = f"codemcp-id:\\s*({CHAT_ID_REGEX})"
