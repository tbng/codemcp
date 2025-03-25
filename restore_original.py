#!/usr/bin/env python3

"""Script to restore the original code in main.py."""

import os

# Path to the main.py file
MAIN_PY_PATH = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "codemcp", "main.py"
)

# Original code snippet
ORIGINAL_CODE = """            content_str = content or ""
            return await write_file_content(path, content_str, description, chat_id)"""

# Modified code with JSON serialization
MODIFIED_CODE = """            import json
            
            # If content is not a string, serialize it to a string using json.dumps
            if content is not None and not isinstance(content, str):
                content_str = json.dumps(content)
            else:
                content_str = content or ""
                
            return await write_file_content(path, content_str, description, chat_id)"""


def restore_original_code():
    """Restore the original code without JSON serialization."""
    with open(MAIN_PY_PATH, "r") as f:
        content = f.read()

    # Replace the modified code with the original
    content = content.replace(MODIFIED_CODE, ORIGINAL_CODE)

    with open(MAIN_PY_PATH, "w") as f:
        f.write(content)

    print(f"Original code restored in {MAIN_PY_PATH}")


if __name__ == "__main__":
    restore_original_code()
