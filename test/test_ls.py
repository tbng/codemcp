#!/usr/bin/env python3

import os
import re
import tempfile
import unittest

from expecttest import TestCase

from codemcp.tools.ls import (
    MAX_FILES,
    TreeNode,
    create_file_tree,
    list_directory,
    ls_directory,
    print_tree,
    skip,
)


class TestLS(TestCase):
    def setUp(self):
        # Create a temporary directory for test files
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)

        # Create a test directory structure
        self.test_dir = os.path.join(self.temp_dir.name, "test_dir")
        os.makedirs(self.test_dir, exist_ok=True)

        # Create some files in the test directory
        self.file1_path = os.path.join(self.test_dir, "file1.txt")
        with open(self.file1_path, "w") as f:
            f.write("This is file 1\n")

        self.file2_path = os.path.join(self.test_dir, "file2.txt")
        with open(self.file2_path, "w") as f:
            f.write("This is file 2\n")

        # Create a subdirectory
        self.subdir_path = os.path.join(self.test_dir, "subdir")
        os.makedirs(self.subdir_path, exist_ok=True)

        # Create a file in the subdirectory
        self.subdir_file_path = os.path.join(self.subdir_path, "subdir_file.txt")
        with open(self.subdir_file_path, "w") as f:
            f.write("This is a file in the subdirectory\n")

        # Create a hidden file
        self.hidden_file_path = os.path.join(self.test_dir, ".hidden_file")
        with open(self.hidden_file_path, "w") as f:
            f.write("This is a hidden file\n")

        # Create a __pycache__ directory
        self.pycache_dir = os.path.join(self.test_dir, "__pycache__")
        os.makedirs(self.pycache_dir, exist_ok=True)
        self.pycache_file_path = os.path.join(self.pycache_dir, "cache_file.pyc")
        with open(self.pycache_file_path, "w") as f:
            f.write("This is a cache file\n")

    def normalize_result(self, result):
        """Normalize temporary directory paths in the result.

        This replaces the actual temporary directory path with a fixed placeholder
        to make tests more stable across different runs.
        """
        if self.temp_dir and self.temp_dir.name:
            # Replace the actual temp dir path with a fixed placeholder
            return re.sub(re.escape(self.temp_dir.name), "/tmp", result)
        return result

    def test_ls_directory_basic(self):
        """Test basic directory listing functionality"""
        result = ls_directory(self.test_dir)
        normalized_result = self.normalize_result(result)

        # Check that the output contains the expected files and directories
        self.assertIn("file1.txt", normalized_result)
        self.assertIn("file2.txt", normalized_result)
        self.assertIn("subdir/", normalized_result)

        # Check that hidden files and __pycache__ are excluded
        self.assertNotIn(".hidden_file", normalized_result)
        self.assertNotIn("__pycache__", normalized_result)

    def test_ls_directory_nonexistent(self):
        """Test listing a nonexistent directory"""
        nonexistent_dir = os.path.join(self.temp_dir.name, "nonexistent")
        result = ls_directory(nonexistent_dir)
        self.assertIn("Error: Directory does not exist", result)

    def test_ls_directory_file(self):
        """Test listing a file instead of a directory"""
        result = ls_directory(self.file1_path)
        self.assertIn("Error: Path is not a directory", result)

    def test_list_directory(self):
        """Test the list_directory function"""
        results = list_directory(self.test_dir)

        # Convert to set for easier comparison
        result_set = set(results)

        # Check that the expected files and directories are included
        self.assertIn("file1.txt", result_set)
        self.assertIn("file2.txt", result_set)
        self.assertIn(f"subdir{os.sep}", result_set)
        self.assertIn(f"subdir{os.sep}subdir_file.txt", result_set)

        # Check that hidden files and __pycache__ are excluded
        self.assertNotIn(".hidden_file", result_set)
        self.assertNotIn("__pycache__", result_set)

    def test_skip(self):
        """Test the skip function"""
        # Hidden files should be skipped
        self.assertTrue(skip(self.hidden_file_path))

        # __pycache__ directories should be skipped
        self.assertTrue(skip(self.pycache_dir))

        # Regular files should not be skipped
        self.assertFalse(skip(self.file1_path))

        # Regular directories should not be skipped
        self.assertFalse(skip(self.subdir_path))

    def test_create_file_tree(self):
        """Test the create_file_tree function"""
        paths = [
            "file1.txt",
            "file2.txt",
            f"subdir{os.sep}",
            f"subdir{os.sep}subdir_file.txt",
        ]
        tree = create_file_tree(paths)

        # Check the root level
        self.assertEqual(len(tree), 3)  # file1.txt, file2.txt, subdir/

        # Find the subdir node
        subdir_node = None
        for node in tree:
            if node.name == "subdir":
                subdir_node = node
                break

        # Check that the subdir node exists and has the correct type
        self.assertIsNotNone(subdir_node)
        self.assertEqual(subdir_node.type, "directory")

        # Check that the subdir node has the correct child
        self.assertEqual(len(subdir_node.children), 1)
        self.assertEqual(subdir_node.children[0].name, "subdir_file.txt")
        self.assertEqual(subdir_node.children[0].type, "file")

    def test_print_tree(self):
        """Test the print_tree function"""
        # Create a simple tree
        root = []
        file1 = TreeNode("file1.txt", "file1.txt", "file")
        file2 = TreeNode("file2.txt", "file2.txt", "file")
        subdir = TreeNode("subdir", "subdir", "directory")
        subdir_file = TreeNode("subdir_file.txt", "subdir/subdir_file.txt", "file")

        root.append(file1)
        root.append(file2)
        root.append(subdir)
        subdir.children.append(subdir_file)

        # Print the tree
        result = print_tree(root, cwd="/test/dir")

        # Check the output
        expected_lines = [
            "- /test/dir/",
            "  - file1.txt",
            "  - file2.txt",
            "  - subdir/",
            "    - subdir_file.txt",
        ]

        for line in expected_lines:
            self.assertIn(line, result)

    def test_max_files_limit(self):
        """Test that the MAX_FILES limit is enforced"""
        # Create a directory with more than MAX_FILES files
        many_files_dir = os.path.join(self.temp_dir.name, "many_files")
        os.makedirs(many_files_dir, exist_ok=True)

        # Create a small number of files for testing (we don't need to create MAX_FILES)
        # We'll mock the list_directory function to return more than MAX_FILES
        for i in range(10):
            file_path = os.path.join(many_files_dir, f"file{i}.txt")
            with open(file_path, "w") as f:
                f.write(f"This is file {i}\n")

        # Create a mock list_directory function that returns more than MAX_FILES
        original_list_directory = list_directory

        try:
            # Replace list_directory with a mock function
            def mock_list_directory(path):
                return [f"file{i}.txt" for i in range(MAX_FILES + 100)]

            # Monkey patch the list_directory function
            import codemcp.tools.ls

            codemcp.tools.ls.list_directory = mock_list_directory

            # Call ls_directory
            result = ls_directory(many_files_dir)

            # Check that the truncation message is included
            self.assertIn(
                f"There are more than {MAX_FILES} files in the directory", result
            )

        finally:
            # Restore the original list_directory function
            codemcp.tools.ls.list_directory = original_list_directory
