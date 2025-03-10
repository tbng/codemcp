#!/bin/bash

# Make the script executable
chmod +x "$0"

# Run just the format tests
python -m pytest test/test_format.py -v
