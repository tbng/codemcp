#!/usr/bin/env python3

import re


def parse_message(message):
    """
    Parse a Git commit message into subject, body, and trailers.

    According to the Git documentation, trailers are:
    - A group of one or more lines that is all trailers, or contains at least one
      Git-generated or user-configured trailer and consists of at least 25% trailers.
    - The group must be preceded by one or more empty (or whitespace-only) lines.
    - The group must either be at the end of the message or be the last non-whitespace
      lines before a line that starts with "---" (the "divider").

    Args:
        message (str): The commit message to parse.

    Returns:
        tuple: (subject, body, trailers) where:
            - subject (str): The first line of the message
            - body (str): The body of the message (may be empty)
            - trailers (dict): A dictionary mapping trailer keys to values
    """
    # Handle empty message
    if not message:
        return "", "", {}

    lines = message.splitlines()

    # Extract subject (first line)
    subject = lines[0] if lines else ""

    # Handle case where there's only a subject
    if len(lines) <= 1:
        return subject, "", {}

    # Find the divider line (---) if any
    message_end = len(lines)
    for i, line in enumerate(lines):
        if line.startswith("---"):
            message_end = i
            break

    # Use the lines after the subject and before the divider
    message_lines = lines[1:message_end]

    # If there are no message lines, return just the subject
    if not message_lines:
        return subject, "", {}

    # Find the trailer block start if any
    trailer_start = find_trailer_block_start(message_lines)

    if trailer_start == -1:
        # No trailer block found, everything after subject is body
        body = "\n".join(message_lines)
        return subject, body, {}

    # Parse trailers
    trailers = parse_trailers(message_lines[trailer_start:])

    # Body is everything between subject and trailers, skip leading newlines
    body_lines = message_lines[:trailer_start]
    # Skip any leading blank lines
    start = 0
    while start < len(body_lines) and not body_lines[start].strip():
        start += 1
    body = "\n".join(body_lines[start:]).rstrip()

    return subject, body, trailers


def find_trailer_block_start(lines):
    """
    Find the start index of the trailer block in a list of lines.

    Args:
        lines (list): List of message lines (without subject and divider).

    Returns:
        int: Index of the first line of the trailer block, or -1 if no trailer block is found.
    """
    # Start from the end and find the last block
    last_block_start = len(lines)

    # Skip trailing empty lines
    while last_block_start > 0 and not lines[last_block_start - 1].strip():
        last_block_start -= 1

    if last_block_start == 0:
        # All lines are empty
        return -1

    # Find the beginning of the last block (preceded by an empty line)
    for i in range(last_block_start - 1, -1, -1):
        if not lines[i].strip():
            # Found a blank line
            # Check if the block after it is a trailer block
            if is_trailer_block(lines[i + 1 : last_block_start]):
                return i + 1
            # Not a trailer block, no need to check further
            return -1

    # No blank line found before the last block
    # Check if the entire message is a trailer block
    return 0 if is_trailer_block(lines[:last_block_start]) else -1


def is_trailer_block(lines):
    """
    Determine if the given lines form a trailer block.

    A block is a trailer block if:
    1. All lines are trailers, or
    2. At least one Git-generated trailer exists and at least 25% of lines are trailers

    Args:
        lines (list): List of lines to check.

    Returns:
        bool: True if the lines form a trailer block, False otherwise.
    """
    # Skip empty lines at the beginning and end
    start = 0
    while start < len(lines) and not lines[start].strip():
        start += 1

    end = len(lines)
    while end > start and not lines[end - 1].strip():
        end -= 1

    if start >= end:
        # All lines are empty
        return False

    # Regex to match a trailer line (token followed by separator and value)
    trailer_re = re.compile(r"^([A-Za-z0-9_-]+)(\s*:\s*)(.*)$")

    # Git-generated trailer prefixes
    git_generated_prefixes = ["Signed-off-by: ", "(cherry picked from commit "]

    trailer_lines = 0
    non_trailer_lines = 0
    has_git_generated_trailer = False

    i = start
    while i < end:
        line = lines[i]

        # Check if it's a continuation line (starts with whitespace)
        if line.strip() and line[0].isspace():
            # Count as part of the previous line, which we've already categorized
            i += 1
            continue

        # Check if it's a git-generated trailer
        is_git_trailer = False
        for prefix in git_generated_prefixes:
            if line.startswith(prefix):
                has_git_generated_trailer = True
                trailer_lines += 1
                is_git_trailer = True
                break

        if not is_git_trailer:
            # Check if it's a regular trailer
            if trailer_re.match(line):
                trailer_lines += 1
            else:
                # Not a trailer line
                non_trailer_lines += 1

        i += 1

    # Determine if it's a trailer block based on the criteria
    return (
        (trailer_lines > 0 and non_trailer_lines == 0)  # All lines are trailers
        or (
            has_git_generated_trailer and trailer_lines * 3 >= non_trailer_lines
        )  # At least 25% trailers with git-generated trailer
    )


def parse_trailers(lines):
    """
    Parse trailer lines into a dictionary.

    Handles continuation lines (lines starting with whitespace) as extensions
    of the previous trailer value.

    Args:
        lines (list): List of trailer lines.

    Returns:
        dict: A dictionary mapping trailer keys to values.
    """
    # Regex to match a trailer line
    trailer_re = re.compile(r"^([A-Za-z0-9_-]+)(\s*:\s*)(.*)$")

    # Git-generated trailer prefixes
    git_generated_prefixes = ["Signed-off-by: ", "(cherry picked from commit "]

    trailers = {}
    current_token = None

    for line in lines:
        # Skip empty lines
        if not line.strip():
            continue

        # Check if it's a continuation line
        if line.strip() and line[0].isspace() and current_token:
            trailers[current_token] += " " + line.strip()
            continue

        # Check if it's a git-generated trailer
        is_git_trailer = False
        for prefix in git_generated_prefixes:
            if line.startswith(prefix):
                token = prefix.strip(": ")
                value = line[len(prefix) :].strip()

                # Handle multiple occurrences of the same token
                if token in trailers:
                    trailers[token] += ", " + value
                else:
                    trailers[token] = value

                current_token = token
                is_git_trailer = True
                break

        if not is_git_trailer:
            # Check if it's a regular trailer
            match = trailer_re.match(line)
            if match:
                token, _, value = match.groups()

                # Handle multiple occurrences of the same token
                if token in trailers:
                    trailers[token] += ", " + value.strip()
                else:
                    trailers[token] = value.strip()

                current_token = token
            else:
                # Not a trailer line, ignore it
                current_token = None

    return trailers
