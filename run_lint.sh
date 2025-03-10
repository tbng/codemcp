#!/bin/bash
set -e

# Format code using Ruff
echo "Running Ruff formatter..."
python -m ruff format codemcp/ test/

# Run Ruff linting
echo "Running Ruff linter..."
python -m ruff check --fix codemcp/ test/

# Less safe autofixes
ruff check --select F401 --select I --select F841 --fix codemcp/ test/

echo "Lint and format completed successfully!"
