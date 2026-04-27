#!/usr/bin/env python3
"""DeerFlow Claude Code skill entry point.

This is the main entry point for invoking the deer-flow agent
directly from Claude Code. The skill:

1. Parses CLI arguments for mode preset and prompt
2. Resolves and validates configuration
3. Creates DeerFlowClient with mode settings
4. Invokes the agent with streaming and prints the response

Usage:
    python skill.py "your prompt here"
    python skill.py --flash "quick task"
    python skill.py --pro "complex task needing planning"
    python skill.py --ultra "task requiring subagent delegation"

For configuration help, see config.example.yaml.
"""

import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

# Ensure lib is importable
sys.path.insert(0, str(Path(__file__).parent))

# Import local modules (always available)
from lib.config import resolve_and_validate_config
from lib.errors import format_error, format_streaming_error, STREAMING_ERRORS
from lib.modes import get_mode_config
from lib.stream import stream_and_print
from lib.tools import log_available_tools, log_mcp_status, check_mcp_tool_availability

# For type hints only
if TYPE_CHECKING:
    from deerflow.client import DeerFlowClient


def _get_deerflow_client() -> "type[DeerFlowClient]":
    """Import and return DeerFlowClient, with helpful error on missing package."""
    try:
        from deerflow.client import DeerFlowClient

        return DeerFlowClient
    except ImportError:
        print(
            """deerflow-harness is not installed. Install with:

    pip install deerflow-harness

or:

    uv add deerflow-harness

For local development, you can also install from workspace:

    pip install -e /path/to/deer-flow/backend/packages/harness
""",
            file=sys.stderr,
        )
        sys.exit(1)


def _log_tools(client_kwargs: dict) -> None:
    """Log available tools and MCP status after client initialization.

    Args:
        client_kwargs: The kwargs passed to DeerFlowClient (contains model info).

    This function handles ImportError gracefully if deerflow-harness is not fully
    configured for tool introspection.
    """
    try:
        from deerflow.tools import get_available_tools
        from deerflow.mcp.cache import get_cached_mcp_tools
        from deerflow.config.extensions_config import ExtensionsConfig

        # Get all tools (built-in + MCP)
        model_name = client_kwargs.get("model_name")
        subagent_enabled = client_kwargs.get("subagent_enabled", False)
        tools = get_available_tools(model_name=model_name, subagent_enabled=subagent_enabled)

        # Log available tools
        log_available_tools(tools)

        # Get MCP tools and server config
        mcp_tools = get_cached_mcp_tools()
        extensions_config = ExtensionsConfig.from_file()
        servers = extensions_config.get_enabled_mcp_servers()

        # Log MCP status
        log_mcp_status(servers, mcp_tools)

        # Check and warn about unavailable MCP tools
        check_mcp_tool_availability(servers, mcp_tools)

    except ImportError:
        # deerflow-harness may not have MCP modules, skip silently
        pass
    except Exception:
        # Tool logging is non-critical, don't fail the skill on error
        pass


def stream_with_error_handling(
    client: "DeerFlowClient",
    prompt: str,
    thread_id: str
) -> str:
    """Stream agent response with comprehensive error handling.

    Handles:
    - GraphRecursionError: Shows actionable guidance
    - KeyboardInterrupt: Clean interrupt with exit code 130
    - Generic errors: Formatted with format_streaming_error

    Args:
        client: DeerFlowClient instance.
        prompt: User prompt to send to the agent.
        thread_id: Thread ID for isolation.

    Returns:
        The final accumulated text response from the AI.

    Raises:
        SystemExit: On any error (exit codes: 1 for error, 130 for interrupt).
    """
    try:
        # Import GraphRecursionError at runtime to avoid import dependency
        from langgraph.errors import GraphRecursionError
    except ImportError:
        # If langgraph not available, create a dummy class for detection
        class GraphRecursionError(Exception):
            """Fallback GraphRecursionError if langgraph not installed."""
            pass

    try:
        return stream_and_print(client, prompt, thread_id)

    except GraphRecursionError:
        print(STREAMING_ERRORS["recursion"], file=sys.stderr)
        sys.exit(1)

    except KeyboardInterrupt:
        print("\n[Interrupted]", file=sys.stderr)
        sys.exit(130)

    except Exception as e:
        print(format_streaming_error(e), file=sys.stderr)
        sys.exit(1)


def parse_args(argv: list[str]) -> tuple[str, str]:
    """Parse CLI arguments for mode and prompt.

    Args:
        argv: Command line arguments (excluding script name).

    Returns:
        Tuple of (mode, prompt) where mode defaults to "standard".

    Raises:
        ValueError: If no prompt is provided.
    """
    mode = "standard"
    args = argv[:]

    # Check for mode flag
    if args and args[0].startswith("--"):
        mode = args.pop(0)[2:]  # Remove "--" prefix

    # Require prompt
    if not args:
        raise ValueError(
            'Usage: deer-flow [--flash|--standard|--pro|--ultra] "prompt"'
        )

    # Join remaining args as prompt
    prompt = " ".join(args)
    return mode, prompt


def main_with_args(argv: list[str]) -> None:
    """Main entry point with explicit args for testing.

    Args:
        argv: Command line arguments (excluding script name).
    """
    try:
        mode, prompt = parse_args(argv)
        config_path = resolve_and_validate_config()
        client_kwargs = get_mode_config(mode)

        # Get DeerFlowClient (will exit if not installed)
        DeerFlowClient = _get_deerflow_client()

        # Create client and invoke agent with streaming
        client = DeerFlowClient(config_path=str(config_path), **client_kwargs)

        # Generate thread_id (stateless by default)
        thread_id = str(uuid.uuid4())

        # Stream with error handling
        stream_with_error_handling(client, prompt, thread_id)

        # Print newline after streaming completes
        print()

    except Exception as e:
        print(format_error(e), file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point from CLI."""
    main_with_args(sys.argv[1:])


if __name__ == "__main__":
    main()
