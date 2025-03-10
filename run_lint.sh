#!/bin/bash
set -e

# Format code using Ruff
echo "Running Ruff formatter..."
python -m ruff format codemcp/ test/

# Run Ruff linting
echo "Running Ruff linter..."

UNSAFE_CODES="F401,F841,I"

python -m ruff check --ignore "$UNSAFE_CODES" --fix codemcp/ test/

# Less safe autofixes
ruff check --select "$UNSAFE_CODES" --unsafe-fixes --fix codemcp/ test/

echo "Lint and format completed successfully!"
