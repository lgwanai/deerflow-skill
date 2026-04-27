#!/bin/bash
# Shell wrapper for deer-flow skill
#
# Usage:
#   ./scripts/chat.sh "hello"
#   ./scripts/chat.sh --flash "quick task"
#   ./scripts/chat.sh --pro "complex task"
#   ./scripts/chat.sh --ultra "parallel subagents"

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Run the skill with all arguments passed through
python "$PROJECT_ROOT/skill.py" "$@"
