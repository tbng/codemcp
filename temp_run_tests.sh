#!/bin/bash

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Run the tests for edit_file.py
python -m pytest test/test_edit_file.py -v