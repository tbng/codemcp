#!/bin/bash
set -e

# Get the directory where the script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Run Ruff linting
echo "Running Ruff linter..."

UNSAFE_CODES="F401,F841,I"

"${SCRIPT_DIR}/.venv/bin/python" -m ruff check --ignore "$UNSAFE_CODES" --fix codemcp

# Less safe autofixes
"${SCRIPT_DIR}/.venv/bin/python" -m ruff check --select "$UNSAFE_CODES" --unsafe-fixes --fix

# Check for direct uses of session.call_tool in e2e tests
echo "Checking for direct use of session.call_tool in e2e tests..."
if git grep -n "session.call_tool" -- e2e/*.py; then
  echo "ERROR: Direct calls to session.call_tool detected in e2e tests."
  echo "Please use call_tool_assert_success or call_tool_assert_error helpers instead."
  exit 1
fi

echo "Lint completed successfully!"
