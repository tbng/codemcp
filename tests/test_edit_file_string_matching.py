#!/usr/bin/env python3

import unittest

from codemcp.tools.edit_file import (
    perfect_replace,
    match_but_for_leading_whitespace,
    replace_part_with_missing_leading_whitespace,
    try_dotdotdots,
    replace_closest_edit_distance,
    find_similar_lines,
    replace_most_similar_chunk,
    prep,
    perfect_or_whitespace,
    apply_edit_pure,
)


class TestPerfectReplace(unittest.TestCase):
    def test_exact_match(self):
        whole_lines = ["line1\n", "line2\n", "line3\n", "line4\n"]
        part_lines = ["line2\n", "line3\n"]
        replace_lines = ["replaced2\n", "replaced3\n"]

        result = perfect_replace(whole_lines, part_lines, replace_lines)

        self.assertEqual(result, "line1\nreplaced2\nreplaced3\nline4\n")

    def test_no_match(self):
        whole_lines = ["line1\n", "line2\n", "line3\n", "line4\n"]
        part_lines = ["lineX\n", "lineY\n"]
        replace_lines = ["replaced2\n", "replaced3\n"]

        result = perfect_replace(whole_lines, part_lines, replace_lines)

        self.assertIsNone(result)


class TestMatchButForLeadingWhitespace(unittest.TestCase):
    def test_consistent_leading_whitespace(self):
        whole_lines = ["    line1\n", "    line2\n"]
        part_lines = ["line1\n", "line2\n"]

        result = match_but_for_leading_whitespace(whole_lines, part_lines)

        self.assertEqual(result, "    ")

    def test_inconsistent_leading_whitespace(self):
        whole_lines = ["    line1\n", "  line2\n"]
        part_lines = ["line1\n", "line2\n"]

        result = match_but_for_leading_whitespace(whole_lines, part_lines)

        self.assertIsNone(result)

    def test_content_mismatch(self):
        whole_lines = ["    line1\n", "    line2\n"]
        part_lines = ["line1\n", "different\n"]

        result = match_but_for_leading_whitespace(whole_lines, part_lines)

        self.assertIsNone(result)


class TestReplacePartWithMissingLeadingWhitespace(unittest.TestCase):
    def test_missing_leading_whitespace(self):
        whole_lines = ["    line1\n", "    line2\n", "    line3\n"]
        part_lines = ["line1\n", "line2\n"]
        replace_lines = ["new1\n", "new2\n"]

        result = replace_part_with_missing_leading_whitespace(
            whole_lines, part_lines, replace_lines
        )

        self.assertEqual(result, "    new1\n    new2\n    line3\n")

    def test_no_match(self):
        whole_lines = ["    line1\n", "    lineX\n", "    line3\n"]
        part_lines = ["line1\n", "line2\n"]
        replace_lines = ["new1\n", "new2\n"]

        result = replace_part_with_missing_leading_whitespace(
            whole_lines, part_lines, replace_lines
        )

        self.assertIsNone(result)


class TestTryDotdotdots(unittest.TestCase):
    def test_simple_dots(self):
        whole = "start\nmiddle1\nmiddle2\nend"
        part = "start\n...\nend"
        replace = "start\n...\nnew_end"

        result = try_dotdotdots(whole, part, replace)

        self.assertEqual(result, "start\nmiddle1\nmiddle2\nnew_end")

    def test_no_dots(self):
        whole = "start\nmiddle\nend"
        part = "start\nmiddle\nend"
        replace = "new_start\nnew_middle\nnew_end"

        result = try_dotdotdots(whole, part, replace)

        self.assertIsNone(result)

    def test_unpaired_dots(self):
        whole = "start\nmiddle\nend"
        part = "start\n...\nend"
        replace = "new_start\nnew_end"

        with self.assertRaises(ValueError):
            try_dotdotdots(whole, part, replace)


class TestReplaceClosestEditDistance(unittest.TestCase):
    def test_similar_chunk(self):
        whole_lines = ["line1\n", "line2\n", "lnie3\n", "line4\n"]
        part = "line2\nline3\n"
        part_lines = ["line2\n", "line3\n"]
        replace_lines = ["new2\n", "new3\n"]

        result = replace_closest_edit_distance(
            whole_lines, part, part_lines, replace_lines
        )

        self.assertEqual(result, "line1\nnew2\nnew3\nline4\n")

    def test_below_threshold(self):
        whole_lines = ["line1\n", "line2\n", "completely_different\n", "line4\n"]
        part = "line2\nline3\n"
        part_lines = ["line2\n", "line3\n"]
        replace_lines = ["new2\n", "new3\n"]

        result = replace_closest_edit_distance(
            whole_lines, part, part_lines, replace_lines, similarity_thresh=0.9
        )

        self.assertIsNone(result)


class TestFindSimilarLines(unittest.TestCase):
    def test_find_similar(self):
        search_lines = "line2\nline3"
        content_lines = "line1\nline2\nline3\nline4"

        result = find_similar_lines(search_lines, content_lines)

        # Just check that we get a non-empty result with the expected content
        self.assertTrue(len(result) > 0)
        self.assertTrue("line2" in result and "line3" in result)

    def test_below_threshold(self):
        search_lines = "lineA\nlineB"
        content_lines = "line1\nline2\nline3\nline4"

        result = find_similar_lines(search_lines, content_lines, threshold=0.9)

        self.assertEqual(result, "")


class TestReplaceMoreSimilarChunk(unittest.TestCase):
    def test_perfect_match(self):
        whole = "line1\nline2\nline3\nline4"
        part = "line2\nline3"
        replace = "new2\nnew3"

        result = replace_most_similar_chunk(whole, part, replace)

        self.assertEqual(result, "line1\nnew2\nnew3\nline4\n")

    def test_whitespace_flexible(self):
        whole = "line1\n    line2\n    line3\nline4"
        part = "line2\nline3"
        replace = "new2\nnew3"

        result = replace_most_similar_chunk(whole, part, replace)

        self.assertEqual(result, "line1\n    new2\n    new3\nline4\n")

    def test_dotdots(self):
        whole = "line1\nline2\nmiddle\nline3\nline4"
        part = "line2\n...\nline3"
        replace = "new2\n...\nnew3"

        result = replace_most_similar_chunk(whole, part, replace)

        self.assertEqual(result, "line1\nnew2\nmiddle\nnew3\nline4\n")

    def test_fuzzy_match(self):
        whole = "line1\nline2\nlnie3\nline4"
        part = "line2\nline3"
        replace = "new2\nnew3"

        result = replace_most_similar_chunk(whole, part, replace)

        self.assertEqual(result, "line1\nnew2\nnew3\nline4\n")


class TestPrep(unittest.TestCase):
    def test_prep_with_newline(self):
        content = "line1\nline2\n"

        result, lines = prep(content)

        self.assertEqual(result, "line1\nline2\n")
        self.assertEqual(lines, ["line1\n", "line2\n"])

    def test_prep_without_newline(self):
        content = "line1\nline2"

        result, lines = prep(content)

        self.assertEqual(result, "line1\nline2\n")
        self.assertEqual(lines, ["line1\n", "line2\n"])


class TestPerfectOrWhitespace(unittest.TestCase):
    def test_perfect_match(self):
        whole_lines = ["line1\n", "line2\n", "line3\n"]
        part_lines = ["line2\n", "line3\n"]
        replace_lines = ["new2\n", "new3\n"]

        result = perfect_or_whitespace(whole_lines, part_lines, replace_lines)

        self.assertEqual(result, "line1\nnew2\nnew3\n")

    def test_whitespace_match(self):
        whole_lines = ["line1\n", "    line2\n", "    line3\n"]
        part_lines = ["line2\n", "line3\n"]
        replace_lines = ["new2\n", "new3\n"]

        result = perfect_or_whitespace(whole_lines, part_lines, replace_lines)

        self.assertEqual(result, "line1\n    new2\n    new3\n")

    def test_no_match(self):
        whole_lines = ["line1\n", "lineA\n", "lineB\n"]
        part_lines = ["line2\n", "line3\n"]
        replace_lines = ["new2\n", "new3\n"]

        result = perfect_or_whitespace(whole_lines, part_lines, replace_lines)

        self.assertIsNone(result)


class TestApplyEditPure(unittest.TestCase):
    def test_direct_replacement(self):
        # Test the most common case - direct string replacement
        content = "This is a test string with some content to replace."
        old_string = "with some content"
        new_string = "with new content"

        patch, updated_content = apply_edit_pure(content, old_string, new_string)

        self.assertEqual(
            updated_content, "This is a test string with new content to replace."
        )
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0]["oldLines"], len(old_string.split("\n")))
        self.assertEqual(patch[0]["newLines"], len(new_string.split("\n")))

    def test_create_new_file(self):
        # Test creating new content (empty old_string)
        content = ""
        old_string = ""
        new_string = "This is new content\nwith multiple lines.\n"

        patch, updated_content = apply_edit_pure(content, old_string, new_string)

        self.assertEqual(updated_content, new_string)
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0]["oldLines"], 0)
        self.assertEqual(
            patch[0]["newLines"], 3
        )  # 3 lines including the trailing newline

    def test_no_match_found(self):
        # Test when the old_string is not found in content
        content = "This is existing content.\nIt has multiple lines.\n"
        old_string = "This text doesn't exist in the content"
        new_string = "Replacement that won't be used"

        patch, updated_content = apply_edit_pure(content, old_string, new_string)

        # Should return the original content unchanged
        self.assertEqual(updated_content, content)
        self.assertEqual(len(patch), 0)  # No patch created

    def test_multiline_replacement(self):
        # Test replacing multiple lines
        content = "Line 1\nLine 2\nLine 3\nLine 4\n"
        old_string = "Line 2\nLine 3"
        new_string = "New Line 2\nNew Line 3"

        patch, updated_content = apply_edit_pure(content, old_string, new_string)

        self.assertEqual(updated_content, "Line 1\nNew Line 2\nNew Line 3\nLine 4\n")
        self.assertEqual(len(patch), 1)
        self.assertEqual(patch[0]["oldLines"], 2)
        self.assertEqual(patch[0]["newLines"], 2)
        # Check that the patch has the correct line number
        self.assertEqual(patch[0]["oldStart"], 2)
        self.assertEqual(patch[0]["newStart"], 2)


if __name__ == "__main__":
    unittest.main()
