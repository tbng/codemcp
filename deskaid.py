#!/usr/bin/env python3

import os
import sys
from typing import Optional, Dict, Any, List, Tuple
import mimetypes
import base64
from pathlib import Path

from mcp.server.fastmcp import FastMCP, Context, Image

# Constants
MAX_LINES_TO_READ = 1000
MAX_LINE_LENGTH = 1000

# Initialize FastMCP server
mcp = FastMCP("deskaid")

def is_image_file(file_path: str) -> bool:
    """Check if a file is an image based on its MIME type."""
    mime_type, _ = mimetypes.guess_type(file_path)
    return mime_type is not None and mime_type.startswith('image/')

def get_image_format(file_path: str) -> str:
    """Get the format of an image file."""
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type:
        return mime_type.split('/')[-1]
    return 'png'  # Default format

def read_file_content(file_path: str, offset: Optional[int] = None, limit: Optional[int] = None) -> str:
    """Read a file's content with optional offset and limit."""
    try:
        if not os.path.isabs(file_path):
            return f"Error: File path must be absolute, not relative: {file_path}"
        
        if not os.path.exists(file_path):
            return f"Error: File does not exist: {file_path}"
        
        if os.path.isdir(file_path):
            return f"Error: Path is a directory, not a file: {file_path}"
        
        # Handle image files
        if is_image_file(file_path):
            return f"This is an image file. Use the deskaid tool to view it."
        
        # Handle text files
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            if offset is not None:
                # Skip offset lines
                for _ in range(offset):
                    if not f.readline():
                        break
            
            lines = []
            line_count = 0
            max_lines = MAX_LINES_TO_READ if limit is None else limit
            
            for line in f:
                if line_count >= max_lines:
                    lines.append(f"... (file truncated, reached {max_lines} line limit)")
                    break
                
                # Truncate long lines
                if len(line) > MAX_LINE_LENGTH:
                    lines.append(line[:MAX_LINE_LENGTH] + "... (line truncated)")
                else:
                    lines.append(line)
                
                line_count += 1
            
            return ''.join(lines)
    except Exception as e:
        return f"Error reading file: {str(e)}"

def write_file_content(file_path: str, content: str) -> str:
    """Write content to a file."""
    try:
        if not os.path.isabs(file_path):
            return f"Error: File path must be absolute, not relative: {file_path}"
        
        # Ensure the directory exists
        directory = os.path.dirname(file_path)
        if not os.path.exists(directory):
            return f"Error: Directory does not exist: {directory}"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"Successfully wrote to {file_path}"
    except Exception as e:
        return f"Error writing file: {str(e)}"

def edit_file_content(file_path: str, old_string: str, new_string: str) -> str:
    """Edit a file by replacing old_string with new_string."""
    try:
        if not os.path.isabs(file_path):
            return f"Error: File path must be absolute, not relative: {file_path}"
        
        if not os.path.exists(file_path) and old_string:
            return f"Error: File does not exist: {file_path}"
        
        # Creating a new file
        if not old_string and not os.path.exists(file_path):
            return write_file_content(file_path, new_string)
        
        # Editing an existing file
        with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
            content = f.read()
        
        # Check for uniqueness of old_string
        if old_string and content.count(old_string) > 1:
            return "Error: The provided text to replace appears multiple times in the file. Please provide more context to uniquely identify the instance to replace."
        
        if old_string and old_string not in content:
            return "Error: The provided text to replace was not found in the file. Make sure it matches exactly, including whitespace and indentation."
        
        # Replace the content
        new_content = content.replace(old_string, new_string, 1)
        
        # Write the modified content back to the file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"Successfully edited {file_path}"
    except Exception as e:
        return f"Error editing file: {str(e)}"

@mcp.tool()
async def deskaid(ctx: Context, command: str, file_path: str, arg1: Optional[str] = None, arg2: Optional[str] = None) -> str:
    """
    This is a multipurpose tool that supports the following subcommands:

    ## ReadFile file_path offset? limit?  
      
    Reads a file from the local filesystem. The file_path parameter must be an absolute path, not a relative path. By default, it reads up to ${MAX_LINES_TO_READ} lines starting from the beginning of the file. You can optionally specify a line offset and limit (especially handy for long files), but it's recommended to read the whole file by not providing these parameters. Any lines longer than ${MAX_LINE_LENGTH} characters will be truncated. For image files, the tool will display the image for you.  
      
    ## WriteFile file_path content  
      
    Write a file to the local filesystem. Overwrites the existing file if there is one.  
      
    Before using this tool:  
      
    1. Use the ReadFile tool to understand the file's contents and context  
      
    2. Directory Verification (only applicable when creating new files):  
       - Use the LS tool to verify the parent directory exists and is the correct location  
      
    ## EditFile file_path old_string new_string  
      
    This is a tool for editing files. For larger edits, use the Write tool to overwrite files.  
      
    Before using this tool:  
      
    1. Use the View tool to understand the file's contents and context  
      
    2. Verify the directory path is correct (only applicable when creating new files):  
       - Use the LS tool to verify the parent directory exists and is the correct location  
      
    To make a file edit, provide the following:  
    1. file_path: The absolute path to the file to modify (must be absolute, not relative)  
    2. old_string: The text to replace (must be unique within the file, and must match the file contents exactly, including all whitespace and indentation)  
    3. new_string: The edited text to replace the old_string  
      
    The tool will replace ONE occurrence of old_string with new_string in the specified file.  
      
    CRITICAL REQUIREMENTS FOR USING THIS TOOL:  
      
    1. UNIQUENESS: The old_string MUST uniquely identify the specific instance you want to change. This means:  
       - Include AT LEAST 3-5 lines of context BEFORE the change point  
       - Include AT LEAST 3-5 lines of context AFTER the change point  
       - Include all whitespace, indentation, and surrounding code exactly as it appears in the file  
      
    2. SINGLE INSTANCE: This tool can only change ONE instance at a time. If you need to change multiple instances:  
       - Make separate calls to this tool for each instance  
       - Each call must uniquely identify its specific instance using extensive context  
      
    3. VERIFICATION: Before using this tool:  
       - Check how many instances of the target text exist in the file  
       - If multiple instances exist, gather enough context to uniquely identify each one  
       - Plan separate tool calls for each instance  
      
    WARNING: If you do not follow these requirements:  
       - The tool will fail if old_string matches multiple locations  
       - The tool will fail if old_string doesn't match exactly (including whitespace)  
       - You may change the wrong instance if you don't include enough context  
      
    When making edits:  
       - Ensure the edit results in idiomatic, correct code  
       - Do not leave the code in a broken state  
       - Always use absolute file paths (starting with /)  
      
    If you want to create a new file, use:  
       - A new file path, including dir name if needed  
       - An empty old_string  
       - The new file's contents as new_string  
      
    Remember: when making multiple file edits in a row to the same file, you should prefer to send all edits in a single message with multiple calls to this tool, rather than multiple messages with a single call each.  
    
    Args:
        ctx: The MCP context
        command: The subcommand to execute (ReadFile, WriteFile, EditFile)
        file_path: The path to the file to operate on
        arg1: First optional argument (varies by command)
        arg2: Second optional argument (varies by command)
    """
    if command == "ReadFile":
        # Handle ReadFile command
        offset = int(arg1) if arg1 and arg1.isdigit() else None
        limit = int(arg2) if arg2 and arg2.isdigit() else None
        
        # Check if it's an image file
        if is_image_file(file_path):
            try:
                with open(file_path, 'rb') as f:
                    image_data = f.read()
                    image_format = get_image_format(file_path)
                    return Image(data=image_data, format=image_format)
            except Exception as e:
                return f"Error reading image file: {str(e)}"
        
        # Handle text file
        return read_file_content(file_path, offset, limit)
    
    elif command == "WriteFile":
        # Handle WriteFile command
        content = arg1 or ""
        return write_file_content(file_path, content)
    
    elif command == "EditFile":
        # Handle EditFile command
        old_string = arg1 or ""
        new_string = arg2 or ""
        return edit_file_content(file_path, old_string, new_string)
    
    else:
        return f"Unknown command: {command}. Available commands: ReadFile, WriteFile, EditFile"

if __name__ == "__main__":
    mcp.run()
