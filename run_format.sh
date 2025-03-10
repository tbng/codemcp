#!/bin/bash
set -e

# Format code using Ruff
echo "Running Ruff formatter..."
python -m ruff format codemcp/ test/

echo "Format completed successfully!"
