#!/usr/bin/env python3

"""Script to verify that our test fails before applying the code change."""

import os
import subprocess
import sys

# Path to the main.py file to be modified
MAIN_PY_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "codemcp", "main.py"
)

# Original code snippet that needs to be restored
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


def run_test():
    """Run the test and return the exit code."""
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "e2e/test_json_content_serialization.py",
            "-v",
        ],
        capture_output=True,
    )
    return result


def main():
    # First, restore the original code
    restore_original_code()
    print("Original code restored.")

    # Run the test with original code (should fail)
    print("Running test with original code (expecting failure)...")
    result1 = run_test()

    # Print the output
    print("\nTest output with original code:")
    print(result1.stdout.decode())
    print(result1.stderr.decode())

    print(
        f"Test with original code {'FAILED' if result1.returncode != 0 else 'PASSED'}"
    )
    print(f"Return code: {result1.returncode}")

    return result1.returncode


if __name__ == "__main__":
    sys.exit(main())
