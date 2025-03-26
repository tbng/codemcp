"""Type stubs for tomli package.

This module provides type definitions for the tomli package to help with
type checking when parsing TOML files.
"""

from typing import (
    IO,
    Any,
    Dict,
    List,
    Union,
)

# Define more specific types for TOML data structures
TOMLPrimitive = Union[str, int, float, bool, None]
TOMLArray = List["TOMLValue"]
TOMLTable = Dict[str, "TOMLValue"]
TOMLValue = Union[TOMLPrimitive, TOMLArray, TOMLTable]

# Specific types for command config
CommandList = List[str]
CommandDict = Dict[str, CommandList]
CommandConfig = Union[CommandList, CommandDict]

def load(file_obj: IO[bytes]) -> Dict[str, Any]:
    """Parse a file as TOML and return a dict.

    Args:
        file_obj: A binary file object.

    Returns:
        A dict mapping string keys to complex nested structures of
        strings, ints, floats, lists, and dicts.

    Raises:
        TOMLDecodeError: When a TOML formatted file can't be parsed.
    """
    ...

def loads(s: str) -> Dict[str, Any]:
    """Parse a string as TOML and return a dict.

    Args:
        s: String containing TOML formatted text.

    Returns:
        A dict mapping string keys to complex nested structures of
        strings, ints, floats, lists, and dicts.

    Raises:
        TOMLDecodeError: When a TOML formatted string can't be parsed.
    """
    ...

class TOMLDecodeError(ValueError):
    """Error raised when decoding TOML fails."""

    pass
