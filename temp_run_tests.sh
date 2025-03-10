#!/bin/bash

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Run the tests with verbose output
chmod +x run_trailing_whitespace_tests.sh
./run_trailing_whitespace_tests.sh