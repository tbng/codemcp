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
python codemcp_server.py
```

Install in Claude Desktop:

```bash
mcp install codemcp_server.py
```

Test with MCP Inspector:

```bash
mcp dev codemcp_server.py
```

## Configuration

Deskaid uses a TOML configuration file located at `~/.codemcprc`. Currently supported configuration options:

```toml
[logger]
verbosity = "INFO"  # Can be DEBUG, INFO, WARNING, ERROR, or CRITICAL
```

### Logging

Logs are written to `~/.codemcp/codemcp.log` and to the console. The log level can be set in the configuration file or overridden with environment variables:

- Set the log level in config: `verbosity = "DEBUG"` in `~/.codemcprc`
- Override with environment variable: `DESKAID_DEBUG_LEVEL=DEBUG python -m codemcp`
- Enable debug mode: `DESKAID_DEBUG=1 python -m codemcp`

By default, logs from the 'mcp' module are filtered out to reduce noise. These logs are only shown when running in debug mode (`DESKAID_DEBUG=1`).

Log format:
```
YYYY-MM-DD HH:MM:SS,ms - module_name - LEVEL - Message
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
- An "init" command that will feed the project prompt (per project config)
- Add a system prompt command that will load instructions at the start of
  convo

- Deal with output length limit from Claude Desktop (cannot do an edit longer
  than the limit)
- More faithfully copy claude code's line numbering algorithm
- Stop using catch all exceptions
- Mocks - SUSPICOUS
