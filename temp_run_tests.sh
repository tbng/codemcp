#!/bin/bash

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Run the tests with verbose output
python -m pytest test/test_edit_file.py -v