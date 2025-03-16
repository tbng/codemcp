#!/bin/bash
# Script to install dependencies for development

# Activate virtual environment if it exists
if [ -d ".venv" ]; then
    source .venv/bin/activate
fi

# Install PyYAML
pip install pyyaml

echo "Dependencies installed successfully!"
