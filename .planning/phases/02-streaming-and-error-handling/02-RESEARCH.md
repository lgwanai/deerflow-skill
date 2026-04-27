# Phase 2: Streaming and Error Handling - Research

**Researched:** 2026-04-27
**Domain:** LangGraph streaming patterns, error handling middleware, agent stateless behavior
**Confidence:** HIGH

## Summary

Phase 2 adds token-by-token streaming responses and comprehensive error handling to the deerflow-skill. The architecture leverages `DeerFlowClient.stream()` which yields `StreamEvent` objects with different event types aligned with LangGraph's SSE protocol. Token-level streaming is handled via LangGraph's "messages" mode, which emits content deltas as the model generates tokens.

Error handling is layered: `ToolErrorHandlingMiddleware` catches tool execution errors and converts them to error ToolMessages (allowing the run to continue), while `LLMErrorHandlingMiddleware` provides retry/backoff logic for transient errors and circuit breaker protection. Stateless behavior is the default - each `stream()` or `chat()` call is independent when no checkpointer is provided, which should be clearly documented to users.

**Primary recommendation:** Use `client.stream()` with a "messages-tuple" event handler for real-time token display; wrap the generator in try/except to catch `GraphRecursionError` and LLM errors.

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| STRM-01 | Skill streams agent responses token-by-token | DeerFlowClient.stream() yields messages-tuple events with content deltas; LangGraph "messages" mode emits token-level deltas |
| STRM-02 | Skill handles LangGraph stream events (values, messages-tuple) | StreamEvent types: "values", "messages-tuple", "custom", "end"; each has specific data structure |
| STRM-03 | Skill reports tool execution progress during streaming | messages-tuple events with type="ai" and tool_calls field for tool invocations; type="tool" for results |
| STRM-04 | Skill handles streaming errors gracefully without crashing | Wrap stream loop in try/except; handle GeneratorExit, GraphRecursionError, and generic exceptions |
| ERRR-01 | Skill catches recursion limit exceeded with clear message | GraphRecursionError from LangGraph; catch and format with actionable guidance (config has recursion_limit default=100) |
| ERRR-02 | Skill catches tool execution errors and continues run | ToolErrorHandlingMiddleware converts exceptions to error ToolMessages automatically; no action needed in skill |
| ERRR-03 | Skill catches LLM provider errors with actionable message | LLMErrorHandlingMiddleware handles retries internally; final errors become AIMessages with user-friendly text |
| ERRR-04 | Skill documents stateless behavior (no checkpointer by default) | DeerFlowClient.__init__ checkpointer=None by default; each call is independent; thread_id only for file isolation |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| deerflow-harness | 0.1.0+ | Agent framework | Provides DeerFlowClient with stream() method and StreamEvent types |
| LangGraph | 1.0.6+ | Agent runtime | streaming via stream_mode=["values", "messages", "custom"] |
| Python | 3.12+ | Runtime | Modern async/await, type hints |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langchain-core | 0.3+ | Message types | AIMessage, ToolMessage, HumanMessage for stream event handling |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| DeerFlowClient.stream() | DeerFlowClient.chat() | chat() accumulates internally, no real-time feedback; stream() provides incremental events |
| messages-tuple events | values events only | values gives full snapshots, messages-tuple gives token deltas - both needed for different UX |

## Architecture Patterns

### Recommended Project Structure (Additions)
```
src/
├── lib/
│   ├── stream.py        # Stream event handler and printer
│   └── errors.py        # Extended error formatting (from Phase 1)
├── skill.py             # Modified: use stream() instead of chat()
└── tests/
    ├── test_stream.py   # Streaming behavior tests
    └── test_errors.py   # Extended error handling tests
```

### Pattern 1: Token-by-Token Streaming
**What:** Iterate over StreamEvents and print content deltas to stdout
**When to use:** For real-time user feedback during agent execution
**Example:**
```python
# lib/stream.py
from typing import TYPE_CHECKING
from deerflow.client import DeerFlowClient, StreamEvent

def stream_and_print(client: DeerFlowClient, message: str, thread_id: str | None = None) -> str:
    """Stream agent response, printing tokens as they arrive.
    
    Returns the final accumulated text response.
    """
    chunks: dict[str, list[str]] = {}
    last_id: str = ""
    
    for event in client.stream(message, thread_id=thread_id):
        if event.type == "messages-tuple" and event.data.get("type") == "ai":
            msg_id = event.data.get("id") or ""
            content = event.data.get("content", "")
            
            # Print token delta immediately
            if content:
                print(content, end="", flush=True)
                chunks.setdefault(msg_id, []).append(content)
                last_id = msg_id
            
            # Handle tool calls
            if event.data.get("tool_calls"):
                tool_calls = event.data["tool_calls"]
                for tc in tool_calls:
                    print(f"\n[Calling tool: {tc['name']}]", flush=True)
        
        elif event.type == "messages-tuple" and event.data.get("type") == "tool":
            tool_name = event.data.get("name", "unknown")
            print(f"\n[Tool {tool_name} completed]", flush=True)
    
    return "".join(chunks.get(last_id, []))
```
**Source:** deerflow/client.py lines 467-680 (stream method implementation)

### Pattern 2: Stream Event Types
**What:** Handle different StreamEvent types appropriately
**When to use:** When processing stream output for different UX needs
**Example:**
```python
# StreamEvent types and their data structures:

# "values" - Full state snapshot after each node
event.type == "values"
event.data == {
    "title": str | None,
    "messages": [serialized_message_dict, ...],
    "artifacts": [...]
}

# "messages-tuple" - Per-message update (token deltas)
event.type == "messages-tuple"

# AI text delta
event.data == {"type": "ai", "content": "<delta>", "id": str}

# AI tool call
event.data == {"type": "ai", "content": "", "id": str, "tool_calls": [
    {"name": str, "args": dict, "id": str}
]}

# Tool result
event.data == {
    "type": "tool", 
    "content": str, 
    "name": str, 
    "tool_call_id": str, 
    "id": str
}

# "custom" - Middleware custom events (e.g., llm_retry)
event.type == "custom"
event.data == {"type": "llm_retry", "attempt": int, "wait_ms": int, ...}

# "end" - Stream finished
event.type == "end"
event.data == {"usage": {"input_tokens": int, "output_tokens": int, "total_tokens": int}}
```
**Source:** deerflow/client.py lines 58-77 (StreamEvent dataclass)

### Pattern 3: Error Handling Wrapper
**What:** Wrap stream loop to catch and format errors gracefully
**When to use:** In the main skill.py entry point
**Example:**
```python
# skill.py additions
from langgraph.errors import GraphRecursionError
from lib.errors import format_streaming_error

def stream_with_error_handling(client: DeerFlowClient, message: str, thread_id: str) -> str:
    """Stream with comprehensive error handling."""
    try:
        return stream_and_print(client, message, thread_id)
    
    except GraphRecursionError:
        msg = """The agent reached its maximum reasoning steps (recursion limit).

This usually happens when:
- The task is very complex and requires many tool calls
- The agent is stuck in a loop

What to try:
- Use --pro mode for better planning on complex tasks
- Simplify your request into smaller subtasks
- Check if your query has an answer (some questions have no solution)

Your session context has been preserved. You can continue with a simpler query."""
        print(f"\n{msg}", file=sys.stderr)
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n[Stream interrupted by user]", file=sys.stderr)
        sys.exit(130)  # Standard interrupt exit code
    
    except Exception as e:
        error_msg = format_streaming_error(e)
        print(f"\n{error_msg}", file=sys.stderr)
        sys.exit(1)
```
**Source:** deerflow/client.py RunnableConfig (recursion_limit default 100)

### Pattern 4: Stateless Behavior Documentation
**What:** Inform users about stateless sessions
**When to use:** On first run or in help text
**Example:**
```python
# lib/errors.py addition
STATELESS_SESSION_INFO = """
Note: Each skill invocation is stateless by default.

- Previous conversation turns are NOT remembered
- Tool results from previous calls are NOT available  
- Each call starts fresh with your prompt

For multi-turn conversations, the deer-flow server provides
persistent thread storage. The skill uses embedded mode which
prioritizes simplicity over memory.
"""

# In skill.py or help output:
def print_session_info():
    """Print info about stateless behavior (optional, on first use)."""
    print(STATELESS_SESSION_INFO, file=sys.stderr)
```
**Source:** deerflow/client.py docstring lines 87-94

### Anti-Patterns to Avoid
- **Blocking on full response:** Using chat() when stream() provides better UX
- **Silent error swallowing:** Catching exceptions without printing user guidance
- **Assuming state persistence:** Each stream() call is independent unless checkpointer provided
- **Ignoring tool call events:** User should see when tools are invoked during streaming

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Token streaming | Custom callback handlers | DeerFlowClient.stream() | LangGraph "messages" mode already provides token deltas |
| Tool error handling | Try/except in tool calls | ToolErrorHandlingMiddleware | Converts exceptions to error ToolMessages automatically |
| LLM retry logic | Custom backoff | LLMErrorHandlingMiddleware | Has exponential backoff, circuit breaker, retry-after parsing |
| Stream event parsing | Manual message parsing | StreamEvent dataclass | Standard structure matches LangGraph SSE protocol |

**Key insight:** deerflow-harness provides complete error handling middleware - skill only needs to catch and format top-level exceptions

## Common Pitfalls

### Pitfall 1: GraphRecursionError Not Caught
**What goes wrong:** Agent exceeds recursion_limit (default 100), uncaught exception crashes skill
**Why it happens:** Complex tasks or stuck loops can trigger the limit
**How to avoid:** Wrap stream() call in try/except GraphRecursionError
**Warning signs:** Error message: "GraphRecursionError: Recursion limit"

### Pitfall 2: Tool Errors Crash the Run
**What goes wrong:** Tool execution errors propagate and stop the stream
**Why it happens:** Actually shouldn't happen - ToolErrorHandlingMiddleware catches them
**How to avoid:** Trust the middleware; test that error ToolMessages appear in stream
**Warning signs:** If seeing uncaught tool exceptions, middleware may not be configured

### Pitfall 3: LLM Errors Show Raw Messages
**What goes wrong:** LLM API errors (401, quota, timeout) show raw error text
**Why it happens:** Not wrapping stream in user-friendly error handler
**How to avoid:** Use LLMErrorHandlingMiddleware return messages; these are AIMessages with guidance
**Warning signs:** "APITimeoutError", "AuthenticationError" shown directly to users

### Pitfall 4: Not Flushing stdout
**What goes wrong:** Tokens buffered, appear in chunks instead of streaming
**Why it happens:** Python stdout buffering
**How to avoid:** Use flush=True on print(), or sys.stdout.flush()
**Warning signs:** Output appears in large chunks with delays

## Code Examples

### Complete Streaming Implementation
```python
#!/usr/bin/env python3
"""skill.py - Entry point with streaming support."""
import sys
import uuid
from pathlib import Path
from typing import TYPE_CHECKING

sys.path.insert(0, str(Path(__file__).parent))

from lib.config import resolve_and_validate_config
from lib.errors import format_error, format_streaming_error
from lib.modes import get_mode_config
from lib.stream import stream_and_print

if TYPE_CHECKING:
    from deerflow.client import DeerFlowClient

def _get_deerflow_client() -> "type[DeerFlowClient]":
    try:
        from deerflow.client import DeerFlowClient
        return DeerFlowClient
    except ImportError:
        print("""deerflow-harness is not installed. Install with:

    pip install deerflow-harness
""", file=sys.stderr)
        sys.exit(1)

def stream_with_error_handling(client, prompt: str, thread_id: str) -> str:
    """Stream with comprehensive error handling."""
    from langgraph.errors import GraphRecursionError
    
    try:
        return stream_and_print(client, prompt, thread_id)
    
    except GraphRecursionError:
        print("\nAgent reached recursion limit. Try:"
              "\n  - Simplifying your request"
              "\n  - Using --pro mode for complex tasks",
              file=sys.stderr)
        sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n[Interrupted]", file=sys.stderr)
        sys.exit(130)
    
    except Exception as e:
        print(f"\n{format_streaming_error(e)}", file=sys.stderr)
        sys.exit(1)

def main_with_args(argv: list[str]) -> None:
    try:
        mode, prompt = parse_args(argv)
        config_path = resolve_and_validate_config()
        client_kwargs = get_mode_config(mode)
        
        DeerFlowClient = _get_deerflow_client()
        client = DeerFlowClient(config_path=str(config_path), **client_kwargs)
        
        # Generate thread_id (stateless by default)
        thread_id = str(uuid.uuid4())
        
        # Stream with error handling
        response = stream_with_error_handling(client, prompt, thread_id)
        
        # Ensure newline at end
        print()  # Newline after streaming
        
    except Exception as e:
        print(format_error(e), file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main_with_args(sys.argv[1:])
```

### Stream Event Handler Module
```python
# lib/stream.py
"""Stream event handling and output formatting."""
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deerflow.client import DeerFlowClient

def stream_and_print(client: "DeerFlowClient", message: str, thread_id: str) -> str:
    """Stream agent response with real-time output.
    
    Prints:
    - Token deltas as they arrive
    - Tool call notifications
    - Tool completion notifications
    
    Returns the final accumulated text response.
    """
    chunks: dict[str, list[str]] = {}
    last_id: str = ""
    
    for event in client.stream(message, thread_id=thread_id):
        if event.type == "messages-tuple":
            data = event.data
            
            if data.get("type") == "ai":
                msg_id = data.get("id") or ""
                content = data.get("content", "")
                
                # Print and accumulate token delta
                if content:
                    print(content, end="", flush=True)
                    chunks.setdefault(msg_id, []).append(content)
                    last_id = msg_id
                
                # Tool call notification
                if data.get("tool_calls"):
                    for tc in data["tool_calls"]:
                        print(f"\n[Calling: {tc['name']}]", flush=True)
            
            elif data.get("type") == "tool":
                tool_name = data.get("name", "tool")
                # Optionally print tool result preview
                # result = data.get("content", "")
                # preview = result[:100] + "..." if len(result) > 100 else result
                # print(f"[Result from {tool_name}]", flush=True)
        
        elif event.type == "custom":
            # Handle middleware custom events (e.g., llm_retry)
            if event.data.get("type") == "llm_retry":
                attempt = event.data.get("attempt", 0)
                max_attempts = event.data.get("max_attempts", 3)
                wait_s = event.data.get("wait_ms", 0) / 1000
                print(f"\n[LLM retry {attempt}/{max_attempts}, waiting {wait_s:.0f}s]", 
                      file=sys.stderr, flush=True)
        
        elif event.type == "end":
            # Stream complete - usage stats available in event.data["usage"]
            pass
    
    return "".join(chunks.get(last_id, []))
```

### Extended Error Formatting
```python
# lib/errors.py additions
from langgraph.errors import GraphRecursionError

STREAMING_ERRORS = {
    "recursion": """The agent reached its maximum reasoning steps.

This happens with very complex tasks. Try:
  -- Simplifying your request
  -- Using --pro mode for complex tasks
  
Your session context has been preserved.""",
    
    "llm_timeout": """The LLM provider is taking too long to respond.

This can happen when:
  -- The model is processing a complex request
  -- The provider is experiencing high load

Wait a moment and try again, or use a simpler prompt.""",
    
    "llm_quota": """The LLM provider quota has been exceeded.

Please check your provider account:
  -- OpenAI: https://platform.openai.com/account/usage
  -- Anthropic: https://console.anthropic.com/settings/usage
  
Update billing or wait for quota reset.""",
    
    "llm_auth": """Authentication failed with the LLM provider.

Please check your API key:
  -- Ensure OPENAI_API_KEY or ANTHROPIC_API_KEY is set correctly
  -- Verify the key has not expired
  -- Check that the key has appropriate permissions""",
}

def format_streaming_error(e: Exception) -> str:
    """Format streaming-specific errors with actionable guidance."""
    error_type = type(e).__name__
    error_msg = str(e).lower()
    
    if isinstance(e, GraphRecursionError):
        return STREAMING_ERRORS["recursion"]
    
    if "timeout" in error_msg or "timed out" in error_msg:
        return STREAMING_ERRORS["llm_timeout"]
    
    if "quota" in error_msg or "insufficient" in error_msg:
        return STREAMING_ERRORS["llm_quota"]
    
    if "auth" in error_msg or "unauthorized" in error_msg or "401" in error_msg:
        return STREAMING_ERRORS["llm_auth"]
    
    # LLMErrorHandlingMiddleware already formats most errors into AIMessages
    # that are yielded as stream events. This catches edge cases.
    return f"Agent error: {e}"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| chat() blocking call | stream() with events | deerflow-harness 0.1.0 | Real-time user feedback |
| Raw exception propagation | Middleware-based error handling | deerflow-harness 0.1.0 | Runs continue after tool/LLM errors |
| Manual tool call tracking | messages-tuple with tool_calls | LangGraph 1.0+ | Structured event format |

**Deprecated/outdated:**
- Using chat() for user-facing commands: Use stream() for better UX
- Catching tool exceptions in skill: ToolErrorHandlingMiddleware handles this

## Open Questions

1. **Tool result preview length**
   - What we know: ToolMessage.content can be large
   - What's unclear: How much to show users during streaming
   - Recommendation: Show tool name only, not content (or first 100 chars max)

2. **Custom event handling**
   - What we know: llm_retry events are emitted by LLMErrorHandlingMiddleware
   - What's unclear: Should skill show retry progress to users?
   - Recommendation: Yes, show as [LLM retry N/3, waiting Xs] for transparency

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v --cov=lib` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| STRM-01 | Streams token-by-token | integration | `pytest tests/test_stream.py::test_token_streaming -x` | Wave 0 |
| STRM-02 | Handles values/messages-tuple events | unit | `pytest tests/test_stream.py::test_event_types -x` | Wave 0 |
| STRM-03 | Reports tool execution progress | integration | `pytest tests/test_stream.py::test_tool_progress -x` | Wave 0 |
| STRM-04 | Handles errors gracefully | unit | `pytest tests/test_stream.py::test_error_handling -x` | Wave 0 |
| ERRR-01 | Catches recursion limit | unit | `pytest tests/test_errors.py::test_recursion_limit -x` | Wave 0 |
| ERRR-02 | Tool errors continue run | integration | `pytest tests/test_stream.py::test_tool_error_continues -x` | Wave 0 |
| ERRR-03 | LLM errors actionable message | unit | `pytest tests/test_errors.py::test_llm_errors -x` | Wave 0 |
| ERRR-04 | Documents stateless behavior | unit | `pytest tests/test_errors.py::test_stateless_message -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v --cov=lib`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_stream.py` - streaming behavior tests
- [ ] `tests/test_errors.py` extended - streaming error tests
- [ ] `lib/stream.py` - stream event handler module
- [ ] Mock fixtures for DeerFlowClient.stream() in tests/conftest.py

## Sources

### Primary (HIGH confidence)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/client.py` - DeerFlowClient.stream() implementation (lines 467-680)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/client.py` - StreamEvent dataclass (lines 58-77)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/agents/middlewares/tool_error_handling_middleware.py` - Tool error handling
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/agents/middlewares/llm_error_handling_middleware.py` - LLM error handling with retry/backoff

### Secondary (MEDIUM confidence)
- `/Users/wuliang/workspace/deerflow-skill/skill.py` - Phase 1 implementation (baseline for modification)
- `/Users/wuliang/workspace/deerflow-skill/lib/errors.py` - Phase 1 error formatting (to extend)

### Tertiary (LOW confidence)
- None - all critical information from primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Direct codebase analysis of deerflow-harness
- Architecture: HIGH - StreamEvent and middleware patterns documented in source
- Pitfalls: HIGH - Error handling middleware catches most cases; skill layer adds top-level handling

**Research date:** 2026-04-27
**Valid until:** 30 days (stable LangGraph/Python ecosystem)
