# codemcp

A multi-purpose MCP for coding with Claude Sonnet.  It is specifically
intended to be used with Claude Desktop, where you can purchase Claude Pro and
pay only a flat monthly fee for as much usage up to Anthropic's rate limit, as
opposed to potentially uncapped cost from API usage.

Currently, this MCP only provides the ability to directly read/write files on
your filesystem, based off of Claude Code's tools.  However, it takes an
opinionated approach to implementing this functionality based on the coding
use case:

- Git is mandatory; we generate a commit for every edit so you can easily use
  Git to rollback if the AI does something bad.  The MCP will ONLY write
  to Git tracked files, so you are guaranteed to be able to rollback if
  necessary.

- You must specifically opt-in a repository to being editable with codemcp by
  creating a codemcp.toml file at its base directory.  We will refuse to write
  all other files.

Major missing functionality that I plan to implement ASAP:

- Improve the system prompt

- Linter/autoformatter integration

- Typecheck/build integration

- Test runner integration

- Scrape webpage and add to context

- Explicitly add file to context

- Make file executable tool

- A few more of Claude Code's tools: glob, memory, notebook

Things I NEVER intend to implement, for philosophical reasons:

- Bash tool (instead, I want you to explicitly whitelist commands that are OK
  for the agent to run)

I might write an API-driven version of this tool for when you hit the rate
limit, but it might be better to just get someone to clone an open source
version of Claude Desktop and then iterate off of that.

This tool was bootstrapped into developing itself in three hours.  I'm still
working out Sonnet 3.7's quirks for Python projects, so apologies for any
naughty code.

## Installation

From source:

```bash
uv venv
source .venv/bin/activate
uv sync
```

and then in `claude_desktop_config.json`

```json
{
  "mcpServers": {
    "codemcp": {
      "command": "/Users/ezyang/Dev/codemcp/.venv/bin/python",
      "args": [
        "-m",
        "codemcp"
      ]
    }
  }
}
```

TODO: uvx instructions

There is a pypi package but it is out of date until we get out of rapid
development, install from source for now.

## Usage

Create a project and put this in your system prompt:

```
Before doing anything, first init project PATH_TO_PROJECT.
```

Then chat with Claude about what changes you want to make to the project.

## Configuration

codemcp uses a TOML configuration file located at `~/.codemcprc`. Currently supported configuration options:

```toml
[logger]
verbosity = "INFO"  # Can be DEBUG, INFO, WARNING, ERROR, or CRITICAL
```

In your repository, there is also a config file `codemcp.toml`.

```toml
global_prompt = """
Before beginning work on this feature, write a short haiku.  Do this only once.
"""

[commands]
format = ["./run_format.sh"]
```

The `global_prompt` will be loaded when you initialize the project in chats.

The `commands` section allows you to configure commands for specific tools:
- `format`: The command that will be executed when the Format tool is used to format code according to project standards.

Commands are specified as arrays of strings that will be joined with spaces and executed in a shell context. These commands are not executed directly by Claude, but through dedicated tools provided by codemcp.

When a format command is configured, the system prompt will automatically instruct Claude to use the Format tool when the task is complete.

## Logging

Logs are written to `~/.codemcp/codemcp.log`. The log level can be set in the configuration file or overridden with environment variables:

- Set the log level in config: `verbosity = "DEBUG"` in `~/.codemcprc`
