#!/usr/bin/env python3

import unittest
from codemcp.git import parse_git_commit_message, append_metadata_to_message


class TestGitMessageParsing(unittest.TestCase):
    """Test cases for Git commit message parsing and metadata handling."""

    def test_parse_empty_message(self):
        """Test parsing an empty commit message."""
        message = ""
        main_message, metadata = parse_git_commit_message(message)
        self.assertEqual(main_message, "")
        self.assertEqual(metadata, {})

    def test_parse_simple_message(self):
        """Test parsing a simple commit message without metadata."""
        message = "feat: Add new feature"
        main_message, metadata = parse_git_commit_message(message)
        self.assertEqual(main_message, "feat: Add new feature")
        self.assertEqual(metadata, {})

    def test_parse_message_with_empty_lines(self):
        """Test parsing a message with empty lines but no metadata."""
        message = """feat: Add new feature

This is a longer description

With multiple paragraphs"""
        main_message, metadata = parse_git_commit_message(message)
        self.assertEqual(main_message, message)
        self.assertEqual(metadata, {})

    def test_parse_message_with_codemcp_id(self):
        """Test parsing a message with codemcp-id metadata."""
        message = """feat: Add new feature

This is a description

codemcp-id: abc-123"""
        main_message, metadata = parse_git_commit_message(message)
        self.assertEqual(main_message, "feat: Add new feature\n\nThis is a description")
        self.assertEqual(metadata, {"codemcp-id": "abc-123"})

    def test_parse_message_with_multiple_metadata(self):
        """Test parsing a message with multiple metadata entries."""
        message = """feat: Add feature

Description

codemcp-id: abc-123
Signed-off-by: User <user@example.com>
Co-authored-by: Other <other@example.com>"""
        main_message, metadata = parse_git_commit_message(message)
        self.assertEqual(main_message, "feat: Add feature\n\nDescription")
        self.assertEqual(
            metadata,
            {
                "codemcp-id": "abc-123",
                "Signed-off-by": "User <user@example.com>",
                "Co-authored-by": "Other <other@example.com>",
            },
        )

    def test_parse_message_with_non_standard_metadata(self):
        """Test parsing a message with non-standard metadata."""
        message = """feat: Add feature

Description

codemcp-id: abc-123
Refs: #123
Reviewed-by: Someone"""
        main_message, metadata = parse_git_commit_message(message)
        self.assertEqual(main_message, "feat: Add feature\n\nDescription")
        self.assertEqual(
            metadata,
            {"codemcp-id": "abc-123", "Refs": "#123", "Reviewed-by": "Someone"},
        )

    def test_parse_message_with_embedded_colons(self):
        """Test parsing a message with colons in the main message."""
        message = """feat: Add feature with a: colon

Description: with more: colons

codemcp-id: abc-123"""
        main_message, metadata = parse_git_commit_message(message)
        self.assertEqual(
            main_message,
            "feat: Add feature with a: colon\n\nDescription: with more: colons",
        )
        self.assertEqual(metadata, {"codemcp-id": "abc-123"})

    def test_append_new_metadata(self):
        """Test appending new metadata to a message without existing metadata."""
        message = "feat: Add feature\n\nDescription"
        new_message = append_metadata_to_message(message, {"codemcp-id": "abc-123"})
        self.assertEqual(
            new_message, "feat: Add feature\n\nDescription\n\ncodemcp-id: abc-123"
        )

    def test_append_to_existing_metadata(self):
        """Test appending metadata to a message with existing metadata."""
        message = """feat: Add feature

Description

Signed-off-by: User <user@example.com>"""
        new_message = append_metadata_to_message(message, {"codemcp-id": "abc-123"})
        self.assertEqual(
            new_message,
            """feat: Add feature

Description

Signed-off-by: User <user@example.com>
codemcp-id: abc-123""",
        )

    def test_update_existing_metadata(self):
        """Test updating existing metadata in a message."""
        message = """feat: Add feature

Description

codemcp-id: old-id
Signed-off-by: User <user@example.com>"""
        new_message = append_metadata_to_message(message, {"codemcp-id": "new-id"})
        self.assertEqual(
            new_message,
            """feat: Add feature

Description

Signed-off-by: User <user@example.com>
codemcp-id: new-id""",
        )

    def test_metadata_with_multiline_values(self):
        """Test handling metadata with multiline values."""
        message = """feat: Add feature

Description

Trailer-key: Line 1
 Line 2
 Line 3
Another-key: value"""
        main_message, metadata = parse_git_commit_message(message)
        self.assertEqual(main_message, "feat: Add feature\n\nDescription")
        self.assertEqual(
            metadata,
            {"Trailer-key": "Line 1\n Line 2\n Line 3", "Another-key": "value"},
        )

    def test_metadata_section_with_blank_lines(self):
        """Test handling metadata section with blank lines."""
        # Note: This is not a valid metadata section as per Git's trailer format
        # because of the blank line between Key1 and Key2
        message = """feat: Add feature

Description

Key1: Value1

Key2: Value2"""
        main_message, metadata = parse_git_commit_message(message)
        # In our implementation, Key1 becomes part of the main message,
        # while Key2 at the end is parsed as metadata
        expected_main = """feat: Add feature

Description

Key1: Value1"""
        expected_metadata = {"Key2": "Value2"}
        self.assertEqual(main_message, expected_main)
        self.assertEqual(metadata, expected_metadata)


if __name__ == "__main__":
    unittest.main()
