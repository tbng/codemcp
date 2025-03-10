#!/bin/bash

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Make our temporary script executable
chmod +x run_trailing_whitespace_tests.sh

# Run the whitespace handling tests
python -m pytest test/test_edit_file.py::TestEditFile::test_edit_file_content_trailing_whitespace_match test/test_edit_file.py::TestEditFile::test_edit_file_content_mixed_whitespace_match -v