#!/usr/bin/env python3

import unittest

from expecttest import TestCase

from codemcp.tools.edit_file import (
    apply_edit_pure,
)


class TestEditFileStringMatching(TestCase):
    def test_exact_match(self):
        # Test exact match replacement (previously in TestPerfectReplace)
        content = "line1\nline2\nline3\nline4\n"
        old_string = "line2\nline3\n"
        new_string = "replaced2\nreplaced3\n"

        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNone(error)
        self.assertExpectedInline(
            updated_content, """line1\nreplaced2\nreplaced3\nline4\n"""
        )
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0]["oldLines"], 3)
        self.assertEqual(patch[0]["newLines"], 3)

    def test_no_match(self):
        # Test no match case (previously in TestPerfectReplace)
        content = "line1\nline2\nline3\nline4\n"
        old_string = "lineX\nlineY\n"
        new_string = "replaced2\nreplaced3\n"

        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNotNone(error)
        self.assertEqual(error, "String to replace not found in file.")
        self.assertExpectedInline(updated_content, """line1\nline2\nline3\nline4\n""")
        self.assertEqual(len(patch), 0)

    def test_trailing_whitespace(self):
        # Test trailing whitespace handling
        content = "  line1\n  line2\n  \n  line3\n  line4\n"
        old_string = "  line2\n\n  line3\n"
        new_string = "  replaced2\n\n  replaced3"

        _, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNone(error)
        self.assertExpectedInline(
            updated_content,
            """\
  line1
  replaced2

  replaced3
  line4
""",
        )

    def test_whitespace_match(self):
        # Test whitespace-flexible matching (previously in TestMatchButForLeadingWhitespace)
        content = "    line1\n    line2\n    line3\n"
        old_string = "line1\nline2\n"
        new_string = "new1\nnew2\n"

        # Note: apply_edit_pure doesn't currently handle whitespace matching
        # This test demonstrates the current behavior
        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNotNone(error)
        self.assertEqual(error, "String to replace not found in file.")
        self.assertExpectedInline(
            updated_content, """    line1\n    line2\n    line3\n"""
        )
        self.assertEqual(len(patch), 0)

    def test_dotdotdots(self):
        # Test handling of ... patterns (previously in TestTryDotdotdots)
        content = "start\nmiddle1\nmiddle2\nend"
        old_string = "start\n...\nend"
        new_string = "start\n...\nnew_end"

        # Note: apply_edit_pure doesn't currently handle ... patterns
        # This test demonstrates the current behavior
        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNotNone(error)
        self.assertEqual(error, "String to replace not found in file.")
        self.assertExpectedInline(updated_content, """start\nmiddle1\nmiddle2\nend""")
        self.assertEqual(len(patch), 0)

    def test_fuzzy_match(self):
        # Test fuzzy matching (previously in TestReplaceClosestEditDistance)
        content = "line1\nline2\nlnie3\nline4\n"
        old_string = "line2\nline3\n"
        new_string = "new2\nnew3\n"

        # Note: apply_edit_pure doesn't currently handle fuzzy matching
        # This test demonstrates the current behavior
        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNotNone(error)
        self.assertEqual(error, "String to replace not found in file.")
        self.assertExpectedInline(updated_content, """line1\nline2\nlnie3\nline4\n""")
        self.assertEqual(len(patch), 0)

    def test_direct_replacement(self):
        # Test direct string replacement (from original TestApplyEditPure)
        content = "This is a test string with some content to replace."
        old_string = "with some content"
        new_string = "with new content"

        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNone(error)
        self.assertExpectedInline(
            updated_content, """This is a test string with new content to replace."""
        )
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0]["oldLines"], 1)
        self.assertEqual(patch[0]["newLines"], 1)

    def test_create_new_file(self):
        # Test creating new content (from original TestApplyEditPure)
        content = ""
        old_string = ""
        new_string = "This is new content\nwith multiple lines.\n"

        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNone(error)
        self.assertExpectedInline(
            updated_content, """This is new content\nwith multiple lines.\n"""
        )
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0]["oldLines"], 0)
        self.assertEqual(patch[0]["newLines"], 3)

    def test_no_match_found(self):
        # Test when the old_string is not found in content (from original TestApplyEditPure)
        content = "This is existing content.\nIt has multiple lines.\n"
        old_string = "This text doesn't exist in the content"
        new_string = "Replacement that won't be used"

        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNotNone(error)
        self.assertEqual(error, "String to replace not found in file.")
        self.assertExpectedInline(
            updated_content, """This is existing content.\nIt has multiple lines.\n"""
        )
        self.assertEqual(len(patch), 0)

    def test_multiline_replacement(self):
        # Test replacing multiple lines (from original TestApplyEditPure)
        content = "Line 1\nLine 2\nLine 3\nLine 4\n"
        old_string = "Line 2\nLine 3"
        new_string = "New Line 2\nNew Line 3"

        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNone(error)
        self.assertExpectedInline(
            updated_content, """Line 1\nNew Line 2\nNew Line 3\nLine 4\n"""
        )
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0]["oldLines"], 2)
        self.assertEqual(patch[0]["newLines"], 2)
        self.assertEqual(patch[0]["oldStart"], 2)
        self.assertEqual(patch[0]["newStart"], 2)

    def test_patch_format(self):
        # Test the format of the patch output
        content = "Line 1\nLine 2\nLine 3\n"
        old_string = "Line 2"
        new_string = "New Line 2"

        patch, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNone(error)
        self.assertExpectedInline(updated_content, """Line 1\nNew Line 2\nLine 3\n""")
        self.assertEqual(len(patch), 1)

        # Test patch structure
        patch_entry = patch[0]
        self.assertEqual(patch_entry["oldStart"], 2)
        self.assertEqual(patch_entry["newStart"], 2)
        self.assertEqual(patch_entry["oldLines"], 1)
        self.assertEqual(patch_entry["newLines"], 1)

        # Test patch lines format - join with newlines for better readability
        self.assertExpectedInline(
            "\n".join(patch_entry["lines"]),
            """-Line 2
+New Line 2""",
        )

    def test_multiple_matches(self):
        # Test handling of multiple matches
        content = "line1\nline2\nline1\nline2\n"
        old_string = "line1\nline2"
        new_string = "replaced1\nreplaced2"

        _, updated_content, error = apply_edit_pure(content, old_string, new_string)

        self.assertIsNotNone(error)
        self.assertTrue(error is not None and "Found 2 matches" in error)
        self.assertExpectedInline(updated_content, """line1\nline2\nline1\nline2\n""")
        self.assertEqual(len(_), 0)


if __name__ == "__main__":
    unittest.main()
