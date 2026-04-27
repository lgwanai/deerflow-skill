"""Subagent delegation configuration and error handling.

This module provides configuration for deer-flow subagent delegation:
- Timeout configuration with clear default (900s)
- Concurrency limit configuration (MAX_CONCURRENT_SUBAGENTS)
- Timeout error formatting with agent identification

Environment variables:
- DEER_FLOW_SUBAGENT_TIMEOUT: Subagent timeout in seconds (default: 900)
- MAX_CONCURRENT_SUBAGENTS: Maximum parallel subagents (default: 3)
"""
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deerflow.client import DeerFlowClient

DEFAULT_SUBAGENT_TIMEOUT = 900  # 15 minutes
DEFAULT_MAX_CONCURRENT_SUBAGENTS = 3


def get_subagent_config() -> dict:
    """Get subagent configuration from environment variables.

    Reads:
    - DEER_FLOW_SUBAGENT_TIMEOUT: Timeout in seconds (default: 900)
    - MAX_CONCURRENT_SUBAGENTS: Max parallel subagents (default: 3)

    Returns:
        Dict with subagent_timeout and max_concurrent_subagents.
    """
    return {
        "subagent_timeout": int(os.getenv("DEER_FLOW_SUBAGENT_TIMEOUT", str(DEFAULT_SUBAGENT_TIMEOUT))),
        "max_concurrent_subagents": get_max_concurrent_subagents(),
    }


def get_max_concurrent_subagents() -> int:
    """Get maximum concurrent subagents limit (SUBA-04).

    Reads MAX_CONCURRENT_SUBAGENTS from environment.
    Falls back to DEFAULT_MAX_CONCURRENT_SUBAGENTS on error.

    Returns:
        Maximum number of subagents that can run in parallel.
    """
    default = DEFAULT_MAX_CONCURRENT_SUBAGENTS
    env_value = os.getenv("MAX_CONCURRENT_SUBAGENTS")

    if env_value is None:
        return default

    try:
        value = int(env_value)
        # Validate reasonable range
        if value < 1:
            return default
        return value
    except ValueError:
        return default


def log_subagent_config() -> None:
    """Log subagent configuration at startup.

    Prints configuration to stderr for user visibility.
    Matches logging pattern from lib/tools.py.
    """
    import sys

    max_concurrent = get_max_concurrent_subagents()
    timeout = int(os.getenv("DEER_FLOW_SUBAGENT_TIMEOUT", str(DEFAULT_SUBAGENT_TIMEOUT)))

    print("\n[Subagent Configuration]", file=sys.stderr, flush=True)
    print(f"  - Max concurrent: {max_concurrent}", file=sys.stderr, flush=True)
    print(f"  - Timeout: {timeout}s", file=sys.stderr, flush=True)


def format_subagent_timeout_error(e: Exception, timeout: int) -> str:
    """Format subagent timeout with agent identification (SUBA-03).

    Args:
        e: The timeout exception.
        timeout: Configured timeout in seconds.

    Returns:
        User-friendly error message with subagent context.
    """
    import re

    error_str = str(e)

    # Try to extract agent name from error message
    # Pattern: "Subagent 'agent_name' timed out"
    match = re.search(r"Subagent\s+['\"]([^'\"]+)['\"]", error_str)
    agent_name = match.group(1) if match else "unknown"

    return (
        f"Subagent '{agent_name}' timed out after {timeout}s.\n"
        f"To increase timeout, set DEER_FLOW_SUBAGENT_TIMEOUT environment variable.\n"
        f"Example: export DEER_FLOW_SUBAGENT_TIMEOUT=1800"
    )