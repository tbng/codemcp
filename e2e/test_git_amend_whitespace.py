#!/usr/bin/env python3

"""Tests for whitespace alignment in Git commit messages when amending."""

import os
import re
import unittest

from codemcp.testing import MCPEndToEndTestCase


class GitAmendWhitespaceTest(MCPEndToEndTestCase):
    """Test the whitespace alignment when HEAD is replaced with commit hash."""

    async def test_whitespace_alignment_on_amend(self):
        """Test that whitespace is aligned correctly when HEAD is replaced with a commit hash."""
        # Create a file to edit multiple times
        test_file_path = os.path.join(self.temp_dir.name, "whitespace_test.txt")
        initial_content = "Initial content for whitespace test"

        # Create the file
        with open(test_file_path, "w") as f:
            f.write(initial_content)

        # Add it to git
        await self.git_run(["add", test_file_path])

        # Commit it
        await self.git_run(["commit", "-m", "Add file for whitespace test"])

        async with self.create_client_session() as session:
            # Define a chat_id for our test
            chat_id = await self.get_chat_id(session)

            # First edit with our chat_id
            await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": test_file_path,
                    "old_string": "Initial content for whitespace test",
                    "new_string": "Modified content for whitespace test - edit 1",
                    "description": "First whitespace test edit",
                    "chat_id": chat_id,
                },
            )

            # Get the commit hash for the first edit
            first_commit_hash = await self.git_run(
                ["rev-parse", "--short", "HEAD"], capture_output=True, text=True
            )

            # Second edit with the same chat_id
            await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": test_file_path,
                    "old_string": "Modified content for whitespace test - edit 1",
                    "new_string": "Modified content for whitespace test - edit 2",
                    "description": "Second whitespace test edit",
                    "chat_id": chat_id,
                },
            )

            # Get the commit message with hash and HEAD
            commit_msg = await self.git_run(
                ["log", "-1", "--pretty=%B"], capture_output=True, text=True
            )

            # Print the commit message for debugging
            print(f"Commit message after second edit:\n{commit_msg}")

            # Extract lines with hash and HEAD
            hash_line = None
            head_line = None

            for line in commit_msg.splitlines():
                if first_commit_hash in line:
                    hash_line = line
                elif "HEAD" in line:
                    head_line = line

            self.assertIsNotNone(
                hash_line, "Could not find commit hash line in message"
            )
            self.assertIsNotNone(head_line, "Could not find HEAD line in message")

            # Instead of trying to find the descriptive text (which won't work for base revision),
            # let's check the alignment by verifying the spacing before the hash and HEAD

            # Extract the prefix before commit hash (should be consistent)
            hash_prefix = hash_line.split(first_commit_hash)[0]

            # Extract the prefix before "HEAD"
            head_prefix = head_line.split("HEAD")[0]

            # Spacing after the hash and HEAD should be consistent
            hash_spacing_after = hash_line[
                len(hash_prefix) + len(first_commit_hash) :
            ].split("(Base")[0]
            head_spacing_after = head_line[len(head_prefix) + 4 :].split("Second")[
                0
            ]  # 4 is length of "HEAD"

            print(f"Hash prefix: '{hash_prefix}', HEAD prefix: '{head_prefix}'")
            print(
                f"Hash spacing after: '{hash_spacing_after}', HEAD spacing after: '{head_spacing_after}'"
            )

            # Verify HEAD has proper padding to align with hash
            # The prefixes should be the same (same starting column)
            self.assertEqual(
                hash_prefix,
                head_prefix,
                f"Hash and HEAD are not aligned at the start. Hash prefix: '{hash_prefix}', HEAD prefix: '{head_prefix}'",
            )

            # Third edit to check multiple aligned entries
            await self.call_tool_assert_success(
                session,
                "codemcp",
                {
                    "subtool": "EditFile",
                    "path": test_file_path,
                    "old_string": "Modified content for whitespace test - edit 2",
                    "new_string": "Modified content for whitespace test - edit 3",
                    "description": "Third whitespace test edit",
                    "chat_id": chat_id,
                },
            )

            # Get the second commit hash
            await self.git_run(
                ["rev-parse", "--short", "HEAD"], capture_output=True, text=True
            )

            # Get the updated commit message with multiple entries
            final_commit_msg = await self.git_run(
                ["log", "-1", "--pretty=%B"], capture_output=True, text=True
            )

            print(f"Commit message after third edit:\n{final_commit_msg}")

            # Verify alignment using regex to extract positions
            lines = final_commit_msg.splitlines()

            # Get all lines containing either a commit hash or HEAD
            hash_lines = [line for line in lines if re.search(r"[0-9a-f]{7}", line)]
            head_line = next((line for line in lines if "HEAD" in line), None)

            # Check that we have at least two hash lines (base revision and second edit) and one HEAD line
            self.assertGreaterEqual(
                len(hash_lines), 2, "Expected at least two hash lines in the message"
            )
            self.assertIsNotNone(head_line, "Could not find HEAD line in message")

            # Extract positions where descriptions start
            desc_positions = []
            for line in hash_lines:
                # Find where the description or "(Base revision)" starts
                if "(Base revision)" in line:
                    desc_positions.append(line.find("(Base"))
                else:
                    # Find the first alphabetic character after the hash
                    match = re.search(r"[0-9a-f]{7}\s+([A-Za-z])", line)
                    if match:
                        desc_positions.append(line.find(match.group(1)))

            # Find where the description starts in the HEAD line
            head_desc_pos = None
            match = re.search(r"HEAD\s+([A-Za-z])", head_line)
            if match:
                head_desc_pos = head_line.find(match.group(1))

            self.assertIsNotNone(
                head_desc_pos, "Could not find description position in HEAD line"
            )

            # Verify all description positions are aligned
            for i, pos in enumerate(desc_positions):
                self.assertEqual(
                    pos,
                    head_desc_pos,
                    f"Description alignment mismatch at position {i}. Expected {head_desc_pos}, got {pos}",
                )


if __name__ == "__main__":
    unittest.main()
