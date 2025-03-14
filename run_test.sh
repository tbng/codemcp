#!/bin/bash
set -e

# Simple check to avoid running codemcp tests from incorrect directories
if [ "$(basename $(git rev-parse --show-toplevel 2>/dev/null || echo 'not-git'))" = "codemcp" ]; then
    SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
    if [ "$(git rev-parse --show-toplevel)" != "$SCRIPT_DIR" ]; then
        echo "Warning: Running tests from a codemcp subdirectory. Changing to repo root."
    fi
fi

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Enable debugging info if the CODEMCP_DEBUG environment variable is set
if [ -n "$CODEMCP_DEBUG" ]; then
    echo "===== run_test.sh DEBUG INFO ====="
    echo "Running from directory: $(pwd)"
    echo "Script directory: $SCRIPT_DIR"
    echo "Test arguments: $@"
    echo "============================="
fi

"${SCRIPT_DIR}/.venv/bin/python" -m pytest --tb=native $@
