#!/usr/bin/env python3

import logging
import os

from ..common import find_git_root
from ..rules import find_applicable_rules

__all__ = [
    "user_prompt",
]


async def user_prompt(user_text: str, chat_id: str | None = None) -> str:
    """Store the user's verbatim prompt text for later use.

    This function processes the user's prompt and applies any relevant cursor rules.

    Args:
        user_text: The user's original prompt verbatim
        chat_id: The unique ID of the current chat session

    Returns:
        A message with any applicable cursor rules
    """
    try:
        logging.info(f"Received user prompt for chat ID {chat_id}: {user_text}")
        
        # Get the current working directory to find repo root
        cwd = os.getcwd()
        repo_root = cwd
        
        # Find git repo root
        while repo_root and not os.path.isdir(os.path.join(repo_root, ".git")):
            parent = os.path.dirname(repo_root)
            if parent == repo_root:  # Reached filesystem root
                repo_root = None
                break
            repo_root = parent
        
        result = "User prompt received"
        
        # If we're in a git repo, look for applicable rules
        if repo_root:
            # Find applicable rules (no file path for UserPrompt)
            applicable_rules, suggested_rules = find_applicable_rules(repo_root)
            
            # If we have applicable rules, add them to the result
            if applicable_rules or suggested_rules:
                result += "\n\n// .cursor/rules results:"
                
                # Add directly applicable rules (alwaysApply=true)
                for rule in applicable_rules:
                    rule_content = f"\n\n// Rule from {os.path.relpath(rule.file_path, repo_root)}:\n{rule.payload}"
                    result += rule_content
                
                # Add suggestions for rules with descriptions
                for description, rule_path in suggested_rules:
                    rel_path = os.path.relpath(rule_path, repo_root)
                    result += f"\n\n// If {description} applies, load {rel_path}"
        
        return result
    except Exception as e:
        logging.warning(f"Exception suppressed in user_prompt: {e!s}", exc_info=True)
        return f"Error processing user prompt: {e!s}"
