"""User context module - simplified version for single-user skill.

The full deer-flow implementation supports multi-user isolation via contextvars.
This simplified version always returns 'default' as the effective user ID.
"""

DEFAULT_USER_ID = "default"


def get_effective_user_id() -> str:
    """Return the default user ID for single-user skill mode."""
    return DEFAULT_USER_ID
