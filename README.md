# Deskaid

## WARNING: DO NOT USE, SAFETY FEATURES NOT IMPLEMENTED YET

An MCP server for file operations that provides tools for reading, writing, and editing files.

## Features

- Read files with optional offset and limit parameters
- Write content to files
- Edit files by replacing specific text
- Support for both text and image files

## Installation

```bash
pip install "mcp[cli]"
```

## Usage

Run the server:

```bash
python deskaid_server.py
```

Install in Claude Desktop:

```bash
mcp install deskaid_server.py
```

Test with MCP Inspector:

```bash
mcp dev deskaid_server.py
```

## Commands

### ReadFile

```
ReadFile file_path [offset] [limit]
```

Reads a file from the local filesystem with optional offset and limit parameters.

### WriteFile

```
WriteFile file_path content
```

Writes content to a file, creating it if it doesn't exist.

### EditFile

```
EditFile file_path old_string new_string
```

Edits a file by replacing old_string with new_string.

## Project Roadmap

- Auto git commit after every edit so rollbacks work
- Prevent edits to files which are not under version control
- Add files to context
- Set a base directory (so absolute paths aren't always required)
- Import Aider system prompts
- Load webpages
- Run tests/lints/typecheck

- LS - only use git ls-files
