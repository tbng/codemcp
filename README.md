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
  Git to rollback if the AI does something bad.  TODO: The MCP will ONLY write
  to Git tracked files, so you are guaranteed to be able to rollback if
  necessary.

- You must specifically opt-in a repository to being editable with codemcp by
  creating a codemcp.toml file at its base directory.  We will refuse to write
  all other files.

Major missing functionality that I plan to implement ASAP:

- Linter/autoformatter integration

- Typecheck/build integration

- Test runner integration

- Scrape webpage and add to context

Things I NEVER intend to implement, for philosophical reasons:

- Bash tool

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

or (TODO: test this actually works)

```bash
mcp install codemcp_server.py
```

TODO: uvx instructions

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

## Logging

Logs are written to `~/.codemcp/codemcp.log`. The log level can be set in the configuration file or overridden with environment variables:

- Set the log level in config: `verbosity = "DEBUG"` in `~/.codemcprc`

## Known problems

- Thinking mode doesn't work too well
- Sonnet 3.7 will try very hard to execute commands, which doesn't work
- You can't do an edit that is larger than Claude Desktop's output size limit.
  If you do hit a limit try "Continue" first.
