#!/bin/bash
set -e

# Run Ruff linting
echo "Running Ruff linter..."

UNSAFE_CODES="F401,F841,I"

python -m ruff check --ignore "$UNSAFE_CODES" --fix codemcp/ test/

# Less safe autofixes
ruff check --select "$UNSAFE_CODES" --unsafe-fixes --fix codemcp/ test/

echo "Lint completed successfully!"
