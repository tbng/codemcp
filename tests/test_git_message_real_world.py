#!/usr/bin/env python3

import re
import unittest
from codemcp.git import append_metadata_to_message


class TestGitMessageRealWorldCases(unittest.TestCase):
    """Test Git commit message handling with real-world examples."""

    def test_complex_commit_message_with_signatures(self):
        """Test appending codemcp-id to a complex commit message with different types of signature trailers."""
        message = """feat(git): Improve commit message handling

This commit enhances the Git commit message parsing logic to handle
various forms of trailers and metadata more robustly. It follows
the Git trailer conventions while ensuring backward compatibility.

The implementation now correctly handles:
- Trailers in the conventional format (Key: Value)
- Multiple trailers with different keys
- Multiline trailer values (with indentation)
- Various signature types used in Git projects

Fixes #123
Closes: #456
Refs: #789

Reviewed-by: John Smith <john@example.com>
Tested-by: Continuous Integration <ci@example.com>
Signed-off-by: Developer <dev@example.com>
Co-authored-by: Collaborator <collab@example.com>"""

        # Test appending new metadata
        new_message = append_metadata_to_message(message, {"codemcp-id": "abc-123456"})

        # Verify the end of the message has our codemcp-id
        self.assertTrue(new_message.endswith("codemcp-id: abc-123456"))

        # The codemcp-id should be on a new line after the existing metadata
        expected_end = """Co-authored-by: Collaborator <collab@example.com>
codemcp-id: abc-123456"""
        self.assertTrue(new_message.endswith(expected_end))

    def test_complex_commit_message_with_existing_codemcp_id(self):
        """Test appending another codemcp-id to a complex commit message that already has one."""
        message = """feat(git): Improve commit message handling

This commit enhances the Git commit message parsing logic.

Reviewed-by: John Smith <john@example.com>
codemcp-id: old-id"""

        # Test appending new metadata
        new_message = append_metadata_to_message(message, {"codemcp-id": "new-id"})

        # Verify the end of the message has our new codemcp-id
        self.assertTrue(new_message.endswith("codemcp-id: new-id"))

        # The new codemcp-id should be on a new line after the existing metadata
        expected_end = """Reviewed-by: John Smith <john@example.com>
codemcp-id: old-id
codemcp-id: new-id"""
        self.assertTrue(new_message.endswith(expected_end))

    def test_codemcp_id_extraction_with_regex(self):
        """Test that the regex used in get_head_commit_chat_id still works after changes."""
        # This test verifies the approach used in get_head_commit_chat_id works
        message = """Subject

Foo desc
Bar bar

codemcp-id: 10-blah

Signed-off-by: foobar
ghstack-id: blahblahblah"""

        # Test that get_head_commit_chat_id would correctly extract the codemcp-id
        # We'll do this by using the regex pattern directly since the function is async
        matches = re.findall(r"codemcp-id:\s*([^\n]*)", message)

        # Verify we found a match and it's the correct value
        self.assertTrue(matches)
        self.assertEqual(matches[-1].strip(), "10-blah")

        # Add a new codemcp-id and make sure it works as expected
        new_message = append_metadata_to_message(message, {"codemcp-id": "new-id"})
        matches = re.findall(r"codemcp-id:\s*([^\n]*)", new_message)
        self.assertEqual(len(matches), 2)
        self.assertEqual(matches[-1].strip(), "new-id")


if __name__ == "__main__":
    unittest.main()
