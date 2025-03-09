#!/bin/bash

# Ensure we're in the project root directory
cd "$(dirname "$0")"

# Run the tests
python -m pytest test/
