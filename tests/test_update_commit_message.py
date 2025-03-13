#!/usr/bin/env python3

import unittest
from codemcp.git_message import update_commit_message_with_description


class TestUpdateCommitMessage(unittest.TestCase):
    """Test cases for updating commit messages with git-revs sections."""

    def test_update_basic_message(self):
        """Test updating a basic message with git-revs section."""
        original_message = """feat: create foo.txt file

Add a file foo.txt with contents foo

```git-revs
be899b1  (Base revision)
HEAD     Add foo.txt with content 'foo'
```

codemcp-id: 79-feat-create-foo-txt-file"""

        expected_message = """feat: create foo.txt file

Add a file foo.txt with contents foo

```git-revs
be899b1  (Base revision)
3245873  Add foo.txt with content 'foo'
HEAD     Add bar.txt with content 'bar'
```

codemcp-id: 79-feat-create-foo-txt-file"""

        updated_message = update_commit_message_with_description(
            current_commit_message=original_message,
            description="Add bar.txt with content 'bar'",
            commit_hash="3245873",
            chat_id="79-feat-create-foo-txt-file",
        )

        self.assertEqual(updated_message, expected_message)

    def test_update_message_with_third_party_metadata(self):
        """Test updating a message with third-party metadata added at the bottom."""
        original_message = """feat: create foo.txt file

Add a file foo.txt with contents foo

```git-revs
be899b1  (Base revision)
HEAD     Add foo.txt with content 'foo'
```

codemcp-id: 79-feat-create-foo-txt-file

ghstack-source-id: 1d28f5b40268b261d658603701a2e55ab545e7f5
Pull Request resolved: https://github.com/ezyang/codemcp/pull/30"""

        expected_message = """feat: create foo.txt file

Add a file foo.txt with contents foo

```git-revs
be899b1  (Base revision)
3245873  Add foo.txt with content 'foo'
HEAD     Add bar.txt with content 'bar'
```

codemcp-id: 79-feat-create-foo-txt-file

ghstack-source-id: 1d28f5b40268b261d658603701a2e55ab545e7f5
Pull Request resolved: https://github.com/ezyang/codemcp/pull/30"""

        updated_message = update_commit_message_with_description(
            current_commit_message=original_message,
            description="Add bar.txt with content 'bar'",
            commit_hash="3245873",
            chat_id="79-feat-create-foo-txt-file",
        )

        self.assertEqual(updated_message, expected_message)


if __name__ == "__main__":
    unittest.main()
