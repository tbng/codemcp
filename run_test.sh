#!/bin/bash
set -e
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
echo "===== run_test.sh DIAGNOSTIC INFO ====="
echo "PWD before cd: $(pwd)"
echo "Script dir: $SCRIPT_DIR"
echo "Args: $@"
echo "===== END DIAGNOSTIC INFO ====="
cd "$SCRIPT_DIR"
echo "PWD after cd: $(pwd)"
"${SCRIPT_DIR}/.venv/bin/python" -m pytest --tb=native $@
