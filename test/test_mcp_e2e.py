#!/usr/bin/env python3

import os
import tempfile
import unittest
import shutil
import asyncio
from pathlib import Path
import sys
import subprocess
from contextlib import asynccontextmanager

from expecttest import TestCase

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


class MCPEndToEndTest(TestCase):
    """End-to-end test for codemcp using MCP client."""

    def setUp(self):
        # Create a temporary directory for testing
        self.temp_dir = tempfile.TemporaryDirectory()
        self.testing_time = "1112911993"  # Fixed timestamp for git
        
        # Initialize environment variables for git
        self.env = os.environ.copy()
        # Set environment variables for reproducible git behavior
        self.env.setdefault("GIT_TERMINAL_PROMPT", "0")
        self.env.setdefault("EDITOR", ":")
        self.env.setdefault("GIT_MERGE_AUTOEDIT", "no")
        self.env.setdefault("LANG", "C")
        self.env.setdefault("LC_ALL", "C")
        self.env.setdefault("PAGER", "cat")
        self.env.setdefault("TZ", "UTC")
        self.env.setdefault("TERM", "dumb")
        # For deterministic commit times
        self.env.setdefault("GIT_AUTHOR_EMAIL", "author@example.com")
        self.env.setdefault("GIT_AUTHOR_NAME", "A U Thor")
        self.env.setdefault("GIT_COMMITTER_EMAIL", "committer@example.com")
        self.env.setdefault("GIT_COMMITTER_NAME", "C O Mitter")
        self.env.setdefault("GIT_COMMITTER_DATE", f"{self.testing_time} -0700")
        self.env.setdefault("GIT_AUTHOR_DATE", f"{self.testing_time} -0700")
        
        # Initialize a git repository in the temp directory
        self.init_git_repo()

    def tearDown(self):
        self.temp_dir.cleanup()

    def init_git_repo(self):
        """Initialize a git repository for testing."""
        subprocess.run(
            ["git", "init"], 
            cwd=self.temp_dir.name, 
            env=self.env, 
            check=True, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE
        )
        
        # Create initial commit
        readme_path = os.path.join(self.temp_dir.name, "README.md")
        with open(readme_path, "w") as f:
            f.write("# Test Repository\n")
        
        subprocess.run(
            ["git", "add", "README.md"], 
            cwd=self.temp_dir.name, 
            env=self.env, 
            check=True
        )
        
        subprocess.run(
            ["git", "commit", "-m", "Initial commit"], 
            cwd=self.temp_dir.name, 
            env=self.env, 
            check=True
        )

    def normalize_path(self, text):
        """Normalize temporary directory paths in output text."""
        if self.temp_dir and self.temp_dir.name:
            # Replace the actual temp dir path with a fixed placeholder
            return text.replace(self.temp_dir.name, "/tmp/test_dir")
        return text

    @asynccontextmanager
    async def create_client_session(self):
        """Create an MCP client session connected to codemcp server."""
        # Set up server parameters for the codemcp MCP server
        server_params = StdioServerParameters(
            command=sys.executable,  # Current Python executable
            args=["-m", "codemcp"],  # Module path to codemcp
            env=self.env,
            cwd=self.temp_dir.name  # Set the working directory to our test directory
        )
        
        # Connect to the server and create a session
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the connection
                await session.initialize()
                yield session

    async def test_list_tools(self):
        """Test listing available tools."""
        async with self.create_client_session() as session:
            tools = await session.list_tools()
            # Verify the codemcp tool is available
            tool_names = [tool.name for tool in tools]
            self.assertIn("codemcp", tool_names)

    async def test_read_file(self):
        """Test the ReadFile command."""
        # Create a test file
        test_file_path = os.path.join(self.temp_dir.name, "test_file.txt")
        test_content = "Test content\nLine 2\nLine 3"
        with open(test_file_path, "w") as f:
            f.write(test_content)
        
        async with self.create_client_session() as session:
            # Call the ReadFile tool
            result = await session.call_tool("codemcp", {
                "command": "ReadFile",
                "file_path": test_file_path
            })
            
            # Normalize the result for easier comparison
            normalized_result = self.normalize_path(result)
            
            # Verify the result includes our file content (ignoring line numbers)
            for line in test_content.splitlines():
                self.assertIn(line, normalized_result)
    
    async def test_read_file_with_offset_limit(self):
        """Test the ReadFile command with offset and limit."""
        # Create a test file with multiple lines
        test_file_path = os.path.join(self.temp_dir.name, "multi_line.txt")
        lines = ["Line 1", "Line 2", "Line 3", "Line 4", "Line 5"]
        with open(test_file_path, "w") as f:
            f.write("\n".join(lines))
        
        async with self.create_client_session() as session:
            # Call the ReadFile tool with offset and limit
            result = await session.call_tool("codemcp", {
                "command": "ReadFile",
                "file_path": test_file_path,
                "offset": "2",  # Start from line 2
                "limit": "2"   # Read 2 lines
            })
            
            # Normalize the result
            normalized_result = self.normalize_path(result)
            
            # Verify we got exactly lines 2-3
            self.assertIn("Line 2", normalized_result)
            self.assertIn("Line 3", normalized_result)
            self.assertNotIn("Line 1", normalized_result)
            self.assertNotIn("Line 4", normalized_result)
    
    async def test_write_file(self):
        """Test the WriteFile command."""
        test_file_path = os.path.join(self.temp_dir.name, "new_file.txt")
        content = "New content\nLine 2"
        
        async with self.create_client_session() as session:
            # Call the WriteFile tool
            result = await session.call_tool("codemcp", {
                "command": "WriteFile",
                "file_path": test_file_path,
                "content": content,
                "description": "Create new file"
            })
            
            # Normalize the result
            normalized_result = self.normalize_path(result)
            
            # Verify the success message
            self.assertIn("Successfully wrote to", normalized_result)
            
            # Verify the file was created with the correct content
            with open(test_file_path, "r") as f:
                file_content = f.read()
            self.assertEqual(file_content, content)
            
            # Verify git state (file should be untracked)
            status = subprocess.check_output(
                ["git", "status"], 
                cwd=self.temp_dir.name, 
                env=self.env
            ).decode()
            
            # Use expect test to verify git status - should show as untracked
            self.assertExpectedInline(
                status,
                """On branch main
Untracked files:
  (use "git add <file>..." to include in what will be committed)
	new_file.txt

nothing added to commit but untracked files present (use "git add" to track)
"""
            )
    
    async def test_edit_file(self):
        """Test the EditFile command."""
        # Create a test file with multiple lines for good context
        test_file_path = os.path.join(self.temp_dir.name, "edit_file.txt")
        original_content = "Line 1\nLine 2\nLine 3\nLine 4\nLine 5\n"
        with open(test_file_path, "w") as f:
            f.write(original_content)
        
        # Add the file to git and commit it
        subprocess.run(["git", "add", "edit_file.txt"], cwd=self.temp_dir.name, env=self.env)
        subprocess.run(["git", "commit", "-m", "Add file for editing"], cwd=self.temp_dir.name, env=self.env)
        
        # Edit the file using the EditFile command with proper context
        old_string = "Line 1\nLine 2\nLine 3\n"
        new_string = "Line 1\nModified Line 2\nLine 3\n"
        
        async with self.create_client_session() as session:
            # Call the EditFile tool
            result = await session.call_tool("codemcp", {
                "command": "EditFile",
                "file_path": test_file_path,
                "old_string": old_string,
                "new_string": new_string,
                "description": "Modify line 2"
            })
            
            # Normalize the result
            normalized_result = self.normalize_path(result)
            
            # Verify the success message
            self.assertIn("Successfully edited", normalized_result)
            
            # Verify the file was edited correctly
            with open(test_file_path, "r") as f:
                file_content = f.read()
            
            expected_content = "Line 1\nModified Line 2\nLine 3\nLine 4\nLine 5\n"
            self.assertEqual(file_content, expected_content)
            
            # Verify git state shows modified file
            status = subprocess.check_output(
                ["git", "status"], 
                cwd=self.temp_dir.name, 
                env=self.env
            ).decode()
            
            # Use expect test to verify git status - should show as modified but not staged
            self.assertExpectedInline(
                status,
                """On branch main
Changes not staged for commit:
  (use "git add <file>..." to update what will be committed)
  (use "git restore <file>..." to discard changes in working directory)
	modified:   edit_file.txt

no changes added to commit (use "git add" and/or "git commit -a")
"""
            )
    
    async def test_ls(self):
        """Test the LS command."""
        # Create a test directory structure
        test_dir = os.path.join(self.temp_dir.name, "test_directory")
        os.makedirs(test_dir)
        
        with open(os.path.join(test_dir, "file1.txt"), "w") as f:
            f.write("Content of file 1")
        
        with open(os.path.join(test_dir, "file2.txt"), "w") as f:
            f.write("Content of file 2")
        
        # Create a subdirectory
        sub_dir = os.path.join(test_dir, "subdirectory")
        os.makedirs(sub_dir)
        
        with open(os.path.join(sub_dir, "subfile.txt"), "w") as f:
            f.write("Content of subfile")
        
        async with self.create_client_session() as session:
            # Call the LS tool
            result = await session.call_tool("codemcp", {
                "command": "LS",
                "file_path": test_dir
            })
            
            # Normalize the result
            normalized_result = self.normalize_path(result)
            
            # Verify the result includes all files and directories
            self.assertIn("file1.txt", normalized_result)
            self.assertIn("file2.txt", normalized_result)
            self.assertIn("subdirectory", normalized_result)


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    
    unittest.main()
