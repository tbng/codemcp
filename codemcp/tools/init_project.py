#!/usr/bin/env python3

import os

import tomli

from ..common import normalize_file_path

__all__ = [
    "init_project",
]


def init_project(directory: str) -> str:
    """Initialize a project by reading the codemcp.toml TOML file and returning
    a combined system prompt.

    Args:
        directory: The directory path containing the codemcp.toml file

    Returns:
        A string containing the system prompt plus any global_prompt from the config

    """
    try:
        # Normalize the directory path
        full_dir_path = normalize_file_path(directory)

        # Validate the directory path
        if not os.path.exists(full_dir_path):
            return f"Error: Directory does not exist: {directory}"

        if not os.path.isdir(full_dir_path):
            return f"Error: Path is not a directory: {directory}"

        # Build path to codemcp.toml file
        rules_file_path = os.path.join(full_dir_path, "codemcp.toml")

        # Default system prompt, cribbed from claude code
        # TODO: Figure out if we want Sonnet to make determinations about what
        # goes in the global prompt.  The current ARCHITECTURE.md rule is
        # mostly to make sure we don't lose important information that was
        # conveyed in chats.
        # TODO: This prompt is pretty long, maybe we want it shorter
        system_prompt = """\
# Tone and style
IMPORTANT: You should minimize output tokens as much as possible while maintaining helpfulness, quality, and accuracy. Only address the specific query or task at hand, avoiding tangential information unless absolutely critical for completing the request. If you can answer in 1-3 sentences or a short paragraph, please do.
IMPORTANT: You should NOT answer with unnecessary preamble or postamble (such as explaining your code or summarizing your action), unless the user asks you to.

# Proactiveness
You are allowed to be proactive, but only when the user asks you to do something. You should strive to strike a balance between:
1. Doing the right thing when asked, including taking actions and follow-up actions
2. Not surprising the user with actions you take without asking
For example, if the user asks you how to approach something, you should do your best to answer their question first, and not immediately jump into taking actions.
3. Do not add additional code explanation summary unless requested by the user. After working on a file, just stop, rather than providing an explanation of what you did.

# Following conventions
When making changes to files, first understand the file's code conventions. Mimic code style, use existing libraries and utilities, and follow existing patterns.
- NEVER assume that a given library is available, even if it is well known. Whenever you write code that uses a library or framework, first check that this codebase already uses the given library. For example, you might look at neighboring files, or check the package.json (or cargo.toml, and so on depending on the language).
- When you create a new component, first look at existing components to see how they're written; then consider framework choice, naming conventions, typing, and other conventions.
- When you edit a piece of code, first look at the code's surrounding context (especially its imports) to understand the code's choice of frameworks and libraries. Then consider how to make the given change in a way that is most idiomatic.
- Always follow security best practices. Never introduce code that exposes or logs secrets and keys. Never commit secrets or keys to the repository.

# Code style
- Do not add comments to the code you write, unless the user asks you to, or the code is complex and requires additional context.

# Tool usage policy
- If you intend to call multiple tools and there are no dependencies between the calls, make all of the independent calls in the same function_calls block.

# Tests
We do NOT support running tests within any code generation commands. When the user asks you to generate tests, just explain how they should test the code themselves.
"""
        global_prompt = ""
        format_command_str = ""

        # Check if codemcp.toml file exists
        if os.path.exists(rules_file_path):
            try:
                with open(rules_file_path, "rb") as f:
                    rules_config = tomli.load(f)

                # Extract global_prompt if it exists
                if "global_prompt" in rules_config:
                    global_prompt = rules_config["global_prompt"]

                # Check if format command is configured
                if "commands" in rules_config and "format" in rules_config["commands"]:
                    format_command = rules_config["commands"]["format"]
                    if isinstance(format_command, list) and format_command:
                        format_command_str = (
                            "\nWhen you are done with your task, run code formatting using the Format tool: `Format "
                            + directory
                            + "`"
                        )
            except Exception as e:
                return f"Error reading codemcp.toml file: {e!s}"

        # Combine system prompt, global prompt, and format command
        combined_prompt = system_prompt
        if global_prompt:
            combined_prompt += "\n\n" + global_prompt
        if format_command_str:
            combined_prompt += format_command_str

        return combined_prompt
    except Exception as e:
        return f"Error initializing project: {e!s}"
