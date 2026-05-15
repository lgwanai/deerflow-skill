"""User context module - simplified version for single-user skill.

The full deer-flow implementation supports multi-user isolation via contextvars.
This simplified version always returns 'default' as the effective user ID.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Optional

if TYPE_CHECKING:
    from langgraph.runtime import Runtime

DEFAULT_USER_ID = "default"
AUTO = object()


def get_effective_user_id() -> str:
    """Return the default user ID for single-user skill mode."""
    return DEFAULT_USER_ID


def resolve_runtime_user_id(
    runtime_or_id: Optional[str | Runtime] = None,  # noqa: PYI041
    *,
    raise_if_unset: bool = True,
) -> str:
    """Resolve user_id from a Runtime object or explicit str — always returns default."""
    if runtime_or_id is None:
        return DEFAULT_USER_ID
    if isinstance(runtime_or_id, str):
        return runtime_or_id
    # Runtime object passed — extract user_id if present
    user = getattr(runtime_or_id, "user_id", None)
    if user:
        return str(user)
    return DEFAULT_USER_ID
