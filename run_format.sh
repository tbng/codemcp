#!/bin/bash
set -e

# Format code using Ruff
echo "Running Ruff formatter..."
# Try with python3 instead of python
python3 -m ruff format codemcp/ test/

echo "Format completed successfully!"