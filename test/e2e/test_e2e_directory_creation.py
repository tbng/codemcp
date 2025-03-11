#!/usr/bin/env python3

"""End-to-end tests for directory creation in WriteFile and EditFile."""

import os
import subprocess
import unittest

from codemcp import MCPEndToEndTestCase


class DirectoryCreationTest(MCPEndToEndTestCase):
    """Test recursive directory creation in WriteFile and EditFile commands."""

    async def test_write_file_nested_directories(self):
        """Test WriteFile can create nested directories."""
        # Create a path with multiple nested directories that don't exist
        nested_path = os.path.join(self.temp_dir.name, "test_nest", "level1", "level2", "level3")
        test_file_path = os.path.join(nested_path, "test_file.txt")
        
        # Verify directory doesn't exist
        self.assertFalse(os.path.exists(nested_path), "Nested directory should not exist initially")
        
        content = "Content in a deeply nested directory"
        
        async with self.create_client_session() as session:
            # Call the WriteFile tool
            result = await session.call_tool(
                "codemcp",
                {
                    "command": "WriteFile",
                    "file_path": test_file_path,
                    "content": content,
                    "description": "Create file in nested directories",
                },
            )
            
            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)
            
            # Verify the success message
            self.assertIn("Successfully wrote to", result_text)
            
            # Verify the directories were created
            self.assertTrue(os.path.exists(nested_path), "Nested directories were not created")
            
            # Verify the file was created with the correct content
            self.assertTrue(os.path.exists(test_file_path), "File was not created")
            with open(test_file_path) as f:
                file_content = f.read()
            self.assertEqual(file_content, content)
            
            # Verify git state (nested directories should be tracked)
            ls_files_output = (
                subprocess.run(
                    ["git", "ls-files", test_file_path],
                    cwd=self.temp_dir.name,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                .stdout.decode()
                .strip()
            )
            
            # The file should be tracked in git
            self.assertTrue(
                ls_files_output,
                "File in nested directories was not tracked in git",
            )

    async def test_edit_file_nested_directories(self):
        """Test EditFile can create nested directories when old_string is empty."""
        # Create a path with multiple nested directories that don't exist
        nested_path = os.path.join(self.temp_dir.name, "edit_nest", "level1", "level2")
        test_file_path = os.path.join(nested_path, "new_file.txt")
        
        # Verify directory doesn't exist
        self.assertFalse(os.path.exists(nested_path), "Nested directory should not exist initially")
        
        content = "Content created in nested directories by EditFile"
        
        async with self.create_client_session() as session:
            # Call the EditFile tool with empty old_string
            result = await session.call_tool(
                "codemcp",
                {
                    "command": "EditFile",
                    "file_path": test_file_path,
                    "old_string": "",
                    "new_string": content,
                    "description": "Create file in nested directories with EditFile",
                },
            )
            
            # Normalize the result
            normalized_result = self.normalize_path(result)
            result_text = self.extract_text_from_result(normalized_result)
            
            # Verify the success message
            self.assertIn("Successfully created", result_text)
            
            # Verify the directories were created
            self.assertTrue(os.path.exists(nested_path), "Nested directories were not created")
            
            # Verify the file was created with the correct content
            self.assertTrue(os.path.exists(test_file_path), "File was not created")
            with open(test_file_path) as f:
                file_content = f.read()
            self.assertEqual(file_content, content)
            
            # Verify git state (file should be committed)
            status = subprocess.check_output(
                ["git", "status"],
                cwd=self.temp_dir.name,
                env=self.env,
            ).decode()
            
            # The working tree should be clean if the changes were automatically committed
            self.assertExpectedInline(
                status,
                """On branch main
nothing to commit, working tree clean
""",
            )
            
            # Verify the file is tracked in git
            ls_files_output = (
                subprocess.run(
                    ["git", "ls-files", test_file_path],
                    cwd=self.temp_dir.name,
                    env=self.env,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    check=False,
                )
                .stdout.decode()
                .strip()
            )
            
            # The file should be tracked in git
            self.assertTrue(
                ls_files_output,
                "File created in nested directories was not tracked in git",
            )


if __name__ == "__main__":
    unittest.main()