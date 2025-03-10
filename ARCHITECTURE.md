# codemcp Architecture

This document provides an overview of the architecture and design decisions of codemcp.

## Project Configuration

The codemcp tool uses a TOML file (`codemcp.toml`) in the project root for configuration. This file has several sections:

### Global Prompt

The `global_prompt` string is included in system prompts to provide project-specific instructions to Claude.

```toml
global_prompt = """
Project-specific instructions for Claude go here.
"""
```

### Commands

The `commands` section specifies commands that can be automatically run by Claude at specific times during task execution. Commands are defined as arrays of strings that will be joined with spaces and executed in a shell context:

```toml
[commands]
format = ["./run_format.sh"]
```

Currently supported commands:
- `format`: Run at the end of a task to format code according to project standards.

## System Integration

When a project is initialized using `InitProject`, codemcp reads the `codemcp.toml` file and constructs a system prompt that includes:

1. Default system instructions
2. The project's `global_prompt`
3. Instructions to run configured commands at appropriate times

For example, if a format command is configured, the system prompt will include an instruction for Claude to run the formatting command when the task is complete.
