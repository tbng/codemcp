#!/bin/bash
set -e

# Format code using Ruff
echo "Running Ruff formatter..."
python -m ruff format codemcp/ test/

# Run Ruff linting (optional)
echo "Running Ruff linter..."
python -m ruff check --fix --select I codemcp/ test/

echo "Lint and format completed successfully!"
