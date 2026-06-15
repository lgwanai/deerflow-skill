#!/bin/bash
# DeerFlow CLI entrypoint
# Usage: ./scripts/chat.sh [--flash|--pro|--ultra] [-c "prompt"] [-o file]
#        ./scripts/chat.sh          # interactive mode

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

if [[ -x "$PROJECT_ROOT/.venv/bin/python" ]]; then
    PYTHON="$PROJECT_ROOT/.venv/bin/python"
elif command -v python3 &>/dev/null; then
    PYTHON="python3"
else
    PYTHON="python"
fi

exec "$PYTHON" "$SCRIPT_DIR/cli.py" "$@"
