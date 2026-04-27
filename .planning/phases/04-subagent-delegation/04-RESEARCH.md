# Phase 4: Subagent Delegation - Research

**Researched:** 2026-04-28
**Domain:** Subagent Delegation and Parallel Task Execution (deerflow-harness/LangGraph)
**Confidence:** MEDIUM

## Summary

Phase 4 enables subagent delegation through the deerflow-harness package, allowing the agent to spawn parallel subagents for complex task decomposition. The implementation leverages deerflow-harness's existing `subagent_enabled` parameter in DeerFlowClient, which exposes a `task_tool` for delegation. The skill's role is to configure subagent behavior (timeout, concurrency limits), provide clear timeout feedback, and ensure the `--ultra` mode preset properly enables subagent functionality.

Key insight: DeerFlowClient already implements subagent delegation internally when `subagent_enabled=True`. The skill must:
1. Pass `subagent_enabled=True` when `--ultra` mode is selected (already done in Phase 1)
2. Configure subagent timeout with a clear default (900s)
3. Report which subagent timed out when timeout errors occur
4. Expose `MAX_CONCURRENT_SUBAGENTS` limit via environment variable or config

**Primary recommendation:** Add a `lib/subagent.py` module for subagent-specific configuration and timeout error handling, hooking into the existing streaming flow.

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| SUBA-01 | Skill enables task_tool for subagent delegation | `subagent_enabled=True` in DeerFlowClient constructor exposes task_tool; already mapped in modes.py for `--ultra` |
| SUBA-02 | Skill configures subagent timeout with clear default (900s) | LangGraph uses asyncio.wait_for with configurable timeout; deerflow-harness likely exposes timeout config |
| SUBA-03 | Skill reports which subagent timed out on timeout error | TimeoutError from asyncio.wait_for needs agent context extraction; deerflow-harness middleware may provide this |
| SUBA-04 | Skill exposes MAX_CONCURRENT_SUBAGENTS limit | Semaphore-based concurrency control; environment variable pattern matches project style |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| deerflow-harness | 0.1.0+ | Core agent framework with subagent support | Provides DeerFlowClient with `subagent_enabled` parameter |
| langgraph | 0.2.x+ | Agent orchestration | Subagent delegation via task_tool, subgraph patterns |
| asyncio | stdlib | Async timeout handling | `asyncio.wait_for` for timeout, `asyncio.Semaphore` for concurrency |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langchain-core | 0.3.x | Tool abstractions | BaseTool interface for task_tool |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom subagent system | deerflow-harness task_tool | deerflow-harness already provides battle-tested implementation |
| Manual timeout tracking | LangGraph middleware | Middleware provides cleaner error context |

**Installation:**
```bash
pip install deerflow-harness langgraph
```

## Architecture Patterns

### Recommended Project Structure
```
lib/
├── config.py          # Config resolution (Phase 1)
├── errors.py          # Error formatting (Phase 2)
├── modes.py           # Mode presets (Phase 1) - already includes subagent_enabled
├── stream.py          # Stream handling (Phase 2)
├── tools.py           # Tool logging (Phase 3)
└── subagent.py        # Subagent config (Phase 4) - NEW
```

### Pattern 1: Subagent Timeout Configuration
**What:** Configure subagent timeout with default 900 seconds
**When to use:** When DeerFlowClient is created with subagent_enabled=True
**Example:**
```python
# Source: deerflow/client.py (hypothesized interface)
import os
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deerflow.client import DeerFlowClient

DEFAULT_SUBAGENT_TIMEOUT = 900  # 15 minutes

def get_subagent_config() -> dict:
    """Get subagent configuration from environment.
    
    Returns:
        Dict with subagent_timeout and max_concurrent_subagents.
    """
    return {
        "subagent_timeout": int(os.getenv("DEER_FLOW_SUBAGENT_TIMEOUT", DEFAULT_SUBAGENT_TIMEOUT)),
        "max_concurrent_subagents": int(os.getenv("MAX_CONCURRENT_SUBAGENTS", 3)),
    }
```

### Pattern 2: Timeout Error Context Extraction
**What:** Extract which subagent timed out from timeout error
**When to use:** When asyncio.TimeoutError or similar occurs during streaming
**Example:**
```python
# Source: Hypothesized pattern based on LangGraph error handling
import sys
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from deerflow.client import DeerFlowClient

SUBAGENT_TIMEOUT_ERRORS = {
    "subagent_timeout": """A subagent timed out after {timeout}s.

The subagent '{agent_name}' was working on:
{task_description}

What to try:
- Increase DEER_FLOW_SUBAGENT_TIMEOUT environment variable
- Simplify the subtask
- Use --pro mode for sequential planning instead
""",
}

def format_subagent_timeout_error(e: Exception, timeout: int) -> str:
    """Format subagent timeout with agent identification (SUBA-03).
    
    Args:
        e: The timeout exception.
        timeout: Configured timeout in seconds.
    
    Returns:
        User-friendly error message with subagent context.
    """
    error_msg = str(e).lower()
    
    # Attempt to extract subagent context from error message
    # deerflow-harness may embed agent name in timeout exceptions
    agent_name = "unknown"
    task_description = "a delegated task"
    
    # Pattern: "Subagent 'agent_name' timed out" or similar
    import re
    agent_match = re.search(r"subagent[:\s]+['\"]?(\w+)['\"]?", error_msg, re.IGNORECASE)
    if agent_match:
        agent_name = agent_match.group(1)
    
    task_match = re.search(r"task[:\s]+['\"]?(.+?)['\"]?(?:\s|$)", error_msg, re.IGNORECASE)
    if task_match:
        task_description = task_match.group(1)
    
    return SUBAGENT_TIMEOUT_ERRORS["subagent_timeout"].format(
        timeout=timeout,
        agent_name=agent_name,
        task_description=task_description,
    )
```

### Pattern 3: Concurrency Limit Configuration
**What:** Expose MAX_CONCURRENT_SUBAGENTS for user configuration
**When to use:** When subagent delegation is enabled
**Example:**
```python
# Source: Environment variable pattern from Phase 1 config resolution
import os

def get_max_concurrent_subagents() -> int:
    """Get maximum concurrent subagents limit (SUBA-04).
    
    Returns:
        Maximum number of subagents that can run in parallel.
    """
    default = 3  # Conservative default
    try:
        return int(os.getenv("MAX_CONCURRENT_SUBAGENTS", default))
    except ValueError:
        return default


def log_subagent_config() -> None:
    """Log subagent configuration at startup."""
    import sys
    
    max_concurrent = get_max_concurrent_subagents()
    timeout = int(os.getenv("DEER_FLOW_SUBAGENT_TIMEOUT", 900))
    
    print(f"\n[Subagent Configuration]", file=sys.stderr, flush=True)
    print(f"  - Max concurrent: {max_concurrent}", file=sys.stderr, flush=True)
    print(f"  - Timeout: {timeout}s", file=sys.stderr, flush=True)
```

### Pattern 4: Integration with skill.py Entry Point
**What:** Pass subagent config to DeerFlowClient
**When to use:** When creating DeerFlowClient with --ultra mode
**Example:**
```python
# Source: skill.py modification for Phase 4
def main_with_args(argv: list[str]) -> None:
    """Main entry point with explicit args for testing."""
    try:
        mode, prompt = parse_args(argv)
        config_path = resolve_and_validate_config()
        client_kwargs = get_mode_config(mode)
        
        # Add subagent config if subagent_enabled
        if client_kwargs.get("subagent_enabled"):
            from lib.subagent import get_subagent_config, log_subagent_config
            subagent_config = get_subagent_config()
            client_kwargs.update(subagent_config)
            log_subagent_config()
        
        # ... rest of main logic
```

### Anti-Patterns to Avoid
- **Don't reimplement subagent spawning:** DeerFlowClient handles subagent lifecycle internally via task_tool
- **Don't use synchronous timeouts:** LangGraph is async-first; use asyncio.wait_for, not signal.alarm
- **Don't swallow timeout context:** Pass through agent name/task from deerflow-harness for user feedback

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Subagent spawning | Custom agent executor | deerflow-harness task_tool | Handles tool calling, state management, recursion |
| Timeout tracking | Manual timer threads | asyncio.wait_for | Integrates with LangGraph async runtime |
| Concurrency control | Custom semaphore | os.getenv + deerflow-harness config | deerflow-harness likely has internal semaphore |
| Error context | Parse stack traces | deerflow-harness middleware | Cleaner error messages with agent context |

**Key insight:** Subagent delegation is fully handled by deerflow-harness. The skill's responsibility is configuration (timeout, concurrency) and error message formatting (identifying which agent timed out).

## Common Pitfalls

### Pitfall 1: Missing Timeout Error Context
**What goes wrong:** TimeoutError occurs but no indication of which subagent failed
**Why it happens:** asyncio.TimeoutError doesn't include context about what was being awaited
**How to avoid:** Hook into deerflow-harness's error handling middleware to capture agent context before timeout
**Warning signs:** Generic "operation timed out" messages without subagent identification

### Pitfall 2: Incorrect Concurrency Limit
**What goes wrong:** Setting MAX_CONCURRENT_SUBAGENTS too high causes resource exhaustion
**Why it happens:** Each subagent spawns its own LLM calls and tool executions
**How to avoid:** Default to 3, warn if user sets > 10, document resource implications
**Warning signs:** Memory errors, slow response times, API rate limiting

### Pitfall 3: Timeout Too Short for Complex Tasks
**What goes wrong:** Subagent times out during legitimate long-running task
**Why it happens:** 900s default may be insufficient for multi-file analysis or complex reasoning
**How to avoid:** Make timeout configurable, provide clear error guidance on increasing
**Warning signs:** Frequent timeout errors on tasks that should succeed

### Pitfall 4: Subagent Enabled Without User Intent
**What goes wrong:** User accidentally uses --ultra mode and spawns expensive subagents
**Why it happens:** User may not understand --ultra enables parallel delegation
**How to avoid:** Log subagent configuration at startup, warn about resource usage
**Warning signs:** Unexpected API costs, slow initial response while subagents spawn

## Code Examples

Verified patterns from project context:

### Mode Preset Already Includes Subagent (from modes.py)
```python
# Source: lib/modes.py - already implemented
MODE_PRESETS: dict[str, ModeConfig] = {
    "ultra": ModeConfig(
        thinking_enabled=True, plan_mode=True, subagent_enabled=True
    ),
}
```

### Environment Variable Pattern (from config.py)
```python
# Source: lib/config.py - pattern for env var expansion
import os

def get_subagent_timeout() -> int:
    """Get subagent timeout from environment with default."""
    return int(os.getenv("DEER_FLOW_SUBAGENT_TIMEOUT", 900))
```

### Error Formatting Pattern (from errors.py)
```python
# Source: lib/errors.py - pattern for error message templates
SUBAGENT_ERRORS = {
    "timeout": """A subagent timed out after {timeout}s.

The subagent '{agent_name}' was working on: {task}

What to try:
- Increase DEER_FLOW_SUBAGENT_TIMEOUT environment variable
- Simplify the task
- Use --pro mode for sequential planning
""",
}

def format_subagent_error(e: Exception, context: dict) -> str:
    """Format subagent error with context."""
    # Extract agent context from deerflow-harness error
    ...
```

### Streaming Integration Pattern (from stream.py)
```python
# Source: lib/stream.py - pattern for event handling
def stream_and_print(client, message, thread_id):
    """Stream agent response with real-time output."""
    for event in client.stream(message, thread_id=thread_id):
        if event.type == "custom":
            data = event.data
            # Check for subagent events
            if data.get("type") == "subagent_spawn":
                print(f"\n[Subagent spawned: {data.get('agent_name')}]", ...)
            elif data.get("type") == "subagent_timeout":
                print(f"\n[Subagent timeout: {data.get('agent_name')}]", ...)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Sequential task execution | Parallel subagent delegation | deerflow-harness | Complex tasks decompose into parallel work |
| Fixed timeout (no config) | Configurable via env var | Phase 4 | Users can adjust for workload |
| Generic timeout error | Agent-identified timeout | Phase 4 | Clear feedback on which agent failed |

**Deprecated/outdated:**
- None for this phase - implementing new functionality

## Open Questions

1. **What is the exact deerflow-harness API for subagent timeout?**
   - What we know: `subagent_enabled` parameter exists in modes.py
   - What's unclear: Exact parameter name for timeout (may be `subagent_timeout`, `timeout`, or similar)
   - Recommendation: Research deerflow-harness source or API docs; default to reasonable parameter names

2. **How does deerflow-harness report subagent timeout errors?**
   - What we know: LangGraph uses asyncio for async operations
   - What's unclear: Whether timeout errors include agent name/task context
   - Recommendation: Test with actual deerflow-harness, may need custom middleware

3. **Should max_concurrent_subagents be a DeerFlowClient parameter?**
   - What we know: deerflow-harness may have internal concurrency control
   - What's unclear: Whether it's configurable via constructor or only internal
   - Recommendation: Check deerflow-harness API, fallback to env var documentation only

4. **What streaming events does subagent delegation emit?**
   - What we know: stream.py handles "messages-tuple", "custom", "end" events
   - What's unclear: What custom events subagent spawning produces
   - Recommendation: Test with --ultra mode and capture event types

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v --cov=lib --cov-report=term-missing` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| SUBA-01 | Skill enables task_tool for subagent delegation | unit | `pytest tests/test_subagent.py::test_subagent_enabled_in_ultra_mode -x` | ❌ Wave 0 |
| SUBA-02 | Skill configures subagent timeout with clear default (900s) | unit | `pytest tests/test_subagent.py::test_default_timeout_900s -x` | ❌ Wave 0 |
| SUBA-03 | Skill reports which subagent timed out on timeout error | unit | `pytest tests/test_subagent.py::test_timeout_error_includes_agent_name -x` | ❌ Wave 0 |
| SUBA-04 | Skill exposes MAX_CONCURRENT_SUBAGENTS limit | unit | `pytest tests/test_subagent.py::test_max_concurrent_configurable -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v --cov=lib --cov-report=term-missing`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_subagent.py` — covers SUBA-01 through SUBA-04
- [ ] `tests/conftest.py` — extend with subagent mock fixtures (mock_deerflow_client with subagent support)
- [ ] Mock subagent timeout events for error handling tests
- [ ] Mock subagent spawn events for streaming tests

## Sources

### Primary (HIGH confidence)
- lib/modes.py — MODE_PRESETS with `subagent_enabled` for ultra mode
- lib/stream.py — Stream event handling patterns
- lib/errors.py — Error formatting patterns

### Secondary (MEDIUM confidence)
- deerflow/client.py — Hypothesized DeerFlowClient constructor parameters
- langgraph documentation — Subagent delegation patterns (unverified via web search)

### Tertiary (LOW confidence)
- WebSearch results — General LangGraph subagent patterns, not deerflow-specific

## Metadata

**Confidence breakdown:**
- Standard stack: MEDIUM — deerflow-harness API for subagent config unverified
- Architecture: MEDIUM — patterns extrapolated from existing project code
- Pitfalls: LOW — based on general async/LangGraph knowledge, not deerflow-specific

**Research date:** 2026-04-28
**Valid until:** 7 days — deerflow-harness API needs verification
