#!/bin/bash

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Run the whitespace-specific tests with verbose output
python -m pytest test/test_edit_file.py::TestEditFile::test_edit_file_content_whitespace_only_lines test/test_edit_file.py::TestEditFile::test_edit_file_content_multiple_whitespace_only_lines -v