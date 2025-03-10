#!/bin/bash

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Run the tests
python -m pytest test/

# To run just the whitespace-only lines tests
# python -m pytest test/test_edit_file.py::TestEditFile::test_edit_file_content_whitespace_only_lines test/test_edit_file.py::TestEditFile::test_edit_file_content_multiple_whitespace_only_lines -v

# To run just the untracked files test
# python -m pytest test/test_write_file.py::TestWriteFile::test_write_file_content_untracked_file -v
