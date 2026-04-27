"""Error message formatting and templates.

This module provides actionable error messages for common failure modes:
- Missing deerflow-harness package
- Missing or invalid config.yaml
- Missing credentials (API keys)

All messages are designed to guide users toward resolution with specific
commands and examples.
"""

# Template for missing deerflow-harness package
MISSING_PACKAGE_MSG = """deerflow-harness is not installed. Install with:

    pip install deerflow-harness

or:

    uv add deerflow-harness

For local development, you can also install from workspace:

    pip install -e /path/to/deer-flow/backend/packages/harness
"""

# Template for missing config.yaml
MISSING_CONFIG_MSG = """config.yaml not found.

I've created config.example.yaml with a template configuration.
Copy it to config.yaml and configure your models:

    cp config.example.yaml config.yaml

Then edit config.yaml to add your API keys.
"""

# Template for missing credentials
MISSING_CREDENTIALS_MSG = """Missing required credentials.

The following environment variables need to be set:
  - OPENAI_API_KEY - Get from https://platform.openai.com/api-keys
  - ANTHROPIC_API_KEY - Get from https://console.anthropic.com/settings/keys

Example config.yaml:
  models:
    - name: gpt-4
      use: langchain_openai:ChatOpenAI
      api_key: "$OPENAI_API_KEY"

    - name: claude-3-sonnet
      use: langchain_anthropic:ChatAnthropic
      api_key: "$ANTHROPIC_API_KEY"

Or set in shell:
  export OPENAI_API_KEY=sk-...
  export ANTHROPIC_API_KEY=sk-ant-...

Tip: Add these to your ~/.zshrc or ~/.bashrc for persistence.
"""


def format_error(e: Exception) -> str:
    """Format an exception into an actionable error message.

    Matches error types to appropriate templates and extracts
    relevant context for guidance.

    Args:
        e: The exception to format.

    Returns:
        A user-friendly error message with actionable guidance.
    """
    error_type = type(e).__name__
    error_msg = str(e).lower()

    # Check for deerflow-harness import errors
    if isinstance(e, (ImportError, ModuleNotFoundError)):
        if "deerflow" in error_msg:
            return MISSING_PACKAGE_MSG
        # Other import errors - show generic message with hint
        return f"Import error: {e}\n\nMake sure all required packages are installed."

    # Check for config-related file not found errors
    if isinstance(e, FileNotFoundError):
        msg = str(e)
        if "config" in msg.lower():
            return MISSING_CONFIG_MSG
        # Generic file not found
        return f"File not found: {e}"

    # Check for credential-related value errors
    if isinstance(e, ValueError):
        msg = str(e)
        if "credential" in msg.lower() or "api_key" in msg.lower():
            # The error message from validate_config already has detailed guidance
            # Pass it through with a prefix
            return f"{msg}\n\nFor more help, see config.example.yaml"
        if "parse" in msg.lower() or "yaml" in msg.lower():
            # Config parsing errors
            return msg
        # Generic value error
        return f"Configuration error: {e}"

    # For all other errors, return the raw message
    # LLM provider errors should be passed through without wrapping
    return str(e)
