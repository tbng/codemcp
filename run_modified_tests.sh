#!/bin/bash

# Make the script executable
chmod +x "$0"

# Run modified tests
python -m pytest test/test_format.py test/test_grep.py test/test_init_project.py -v
