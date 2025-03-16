#!/usr/bin/env python3

import os
import re
import fnmatch
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import yaml

__all__ = [
    "Rule",
    "find_applicable_rules",
    "load_rule_from_file",
    "match_file_with_glob",
]


@dataclass
class Rule:
    """Represents a cursor rule loaded from an MDC file."""

    description: Optional[str]  # Description of when the rule is useful
    globs: Optional[List[str]]  # List of glob patterns to match files
    always_apply: bool  # Whether the rule should always be applied
    payload: str  # The markdown content of the rule
    file_path: str  # Path to the MDC file


def load_rule_from_file(file_path: str) -> Optional[Rule]:
    """Load a rule from an MDC file.

    Args:
        file_path: Path to the MDC file

    Returns:
        A Rule object if the file is valid, None otherwise
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Parse the frontmatter and content
        frontmatter_match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
        if not frontmatter_match:
            return None

        frontmatter_text = frontmatter_match.group(1)
        payload = frontmatter_match.group(2).strip()

        # Parse YAML frontmatter
        frontmatter = yaml.safe_load(frontmatter_text)
        if not isinstance(frontmatter, dict):
            return None

        # Extract rule properties
        description = frontmatter.get("description")

        # Handle globs - can be comma-separated string or a list
        globs_value = frontmatter.get("globs")
        globs: Optional[List[str]] = None
        if globs_value:
            if isinstance(globs_value, str):
                globs = [g.strip() for g in globs_value.split(",")]
            elif isinstance(globs_value, list):
                globs = globs_value

        always_apply = frontmatter.get("alwaysApply", False)

        return Rule(
            description=description,
            globs=globs,
            always_apply=always_apply,
            payload=payload,
            file_path=file_path,
        )
    except Exception:
        # If there's any error parsing the file, return None
        return None


def match_file_with_glob(file_path: str, glob_pattern: str) -> bool:
    """Check if a file path matches a glob pattern.

    Args:
        file_path: Path to check
        glob_pattern: Glob pattern to match against

    Returns:
        True if the file matches the pattern, False otherwise
    """
    # Convert to Path object for consistent handling
    path = Path(file_path)

    # Handle ** pattern (recursive wildcard)
    if "**" in glob_pattern:
        # Split the pattern into parts for matching
        parts = glob_pattern.split("**")
        if len(parts) != 2:
            # We only support simple patterns with one ** for now
            return False

        prefix, suffix = parts

        # Check if the file path starts with the prefix and ends with the suffix
        return (prefix == "" or str(path).startswith(prefix)) and (
            suffix == "" or str(path).endswith(suffix)
        )

    # Use fnmatch for simple glob patterns
    return fnmatch.fnmatch(str(path), glob_pattern)


def find_applicable_rules(
    repo_root: str, file_path: Optional[str] = None
) -> Tuple[List[Rule], List[Tuple[str, str]]]:
    """Find all applicable rules for the given file path.

    Walks up the directory tree from the file path to the repo root,
    looking for .cursor/rules directories and loading MDC files.

    Args:
        repo_root: Root of the repository
        file_path: Optional path to a file to match against rules

    Returns:
        A tuple containing (applicable_rules, suggested_rules)
        - applicable_rules: List of Rule objects that match the file
        - suggested_rules: List of (description, file_path) tuples for rules with descriptions
    """
    applicable_rules: List[Rule] = []
    suggested_rules: List[Tuple[str, str]] = []
    processed_rule_files: Set[str] = set()

    # Normalize paths
    repo_root = os.path.abspath(repo_root)

    # If file_path is provided, walk up from its directory to repo_root
    # Otherwise, just check repo_root
    start_dir = os.path.dirname(os.path.abspath(file_path)) if file_path else repo_root
    current_dir = start_dir

    # Ensure we don't go beyond repo_root
    while current_dir.startswith(repo_root):
        # Look for .cursor/rules directory
        rules_dir = os.path.join(current_dir, ".cursor", "rules")
        if os.path.isdir(rules_dir):
            # Find all MDC files in this directory
            for root, _, files in os.walk(rules_dir):
                for filename in files:
                    if filename.endswith(".mdc"):
                        rule_file_path = os.path.join(root, filename)

                        # Skip if we've already processed this file
                        if rule_file_path in processed_rule_files:
                            continue
                        processed_rule_files.add(rule_file_path)

                        # Load the rule
                        rule = load_rule_from_file(rule_file_path)
                        if rule is None:
                            continue

                        # Check if this rule applies
                        if rule.always_apply:
                            applicable_rules.append(rule)
                        elif file_path and rule.globs:
                            # Check if any glob pattern matches the file
                            for glob_pattern in rule.globs:
                                if match_file_with_glob(file_path, glob_pattern):
                                    applicable_rules.append(rule)
                                    break
                        elif rule.description:
                            # Add to suggested rules if it has a description
                            suggested_rules.append((rule.description, rule_file_path))

        # Move up one directory
        parent_dir = os.path.dirname(current_dir)
        if parent_dir == current_dir:  # We've reached the root
            break
        current_dir = parent_dir

    return applicable_rules, suggested_rules
