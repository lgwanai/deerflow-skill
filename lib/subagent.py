"""Subagent delegation configuration and error handling.

This module provides configuration for deer-flow subagent delegation:
- Timeout configuration (DEER_FLOW_SUBAGENT_TIMEOUT env var, default 900s)
- Concurrency limit from config.yaml subagents.max_concurrent (default 3)
- Timeout error formatting with agent identification
"""
import os
import re


DEFAULT_SUBAGENT_TIMEOUT = 900

SUBAGENT_TIMEOUT_ERRORS = {
    "subagent_timeout": """A subagent timed out after {timeout}s.

    The subagent '{agent_name}' was working on:
    {task_description}

    What to try:
    - Increase DEER_FLOW_SUBAGENT_TIMEOUT environment variable:
      export DEER_FLOW_SUBAGENT_TIMEOUT=1800
    - Simplify the subtask or break it into smaller pieces
    - Use --pro mode for sequential planning instead of parallel execution

    Current timeout: {timeout}s (15 min default)
    """,
}


def get_subagent_timeout() -> int:
    """Get subagent timeout from environment variable, or default."""
    return int(os.getenv("DEER_FLOW_SUBAGENT_TIMEOUT", str(DEFAULT_SUBAGENT_TIMEOUT)))


def log_subagent_config() -> None:
    """Log subagent configuration at startup."""
    import sys

    try:
        from deerflow.config import get_app_config
        config = get_app_config()
        max_concurrent = config.subagents.max_concurrent
    except Exception:
        max_concurrent = 3

    timeout = get_subagent_timeout()

    print("\n[Subagent Configuration]", file=sys.stderr, flush=True)
    print(f"  - Max concurrent: {max_concurrent}", file=sys.stderr, flush=True)
    print(f"  - Timeout: {timeout}s", file=sys.stderr, flush=True)


def format_subagent_timeout_error(e: Exception, timeout: int) -> str:
    """Format subagent timeout with agent identification."""
    error_msg = str(e).lower()

    agent_name = "unknown"
    task_description = "a delegated task"

    agent_match = re.search(
        r"subagent[:\s]+['\"]?(\w+)['\"]?",
        error_msg,
        re.IGNORECASE
    )
    if agent_match:
        agent_name = agent_match.group(1)

    task_match = re.search(
        r"(?:task|working on)[:\s]+['\"]?(.+?)['\"]?(?:\s|$)",
        error_msg,
        re.IGNORECASE
    )
    if task_match:
        task_description = task_match.group(1).strip()

    return SUBAGENT_TIMEOUT_ERRORS["subagent_timeout"].format(
        timeout=timeout,
        agent_name=agent_name,
        task_description=task_description,
    )


def is_subagent_timeout(e: Exception) -> bool:
    """Check if exception is a subagent timeout error."""
    error_type = type(e).__name__
    error_msg = str(e).lower()

    if "subagent" in error_msg and ("timeout" in error_msg or "timed out" in error_msg):
        return True

    if error_type in ("TimeoutError", "asyncio.TimeoutError"):
        return "subagent" in error_msg or "task_tool" in error_msg

    return False
