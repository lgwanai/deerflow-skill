# Phase 3: Tool Registry Exposure - Research

**Researched:** 2026-04-27
**Domain:** Tool Registry and MCP Integration (deerflow-harness)
**Confidence:** HIGH

## Summary

Phase 3 requires exposing deer-flow's tool ecosystem through the Claude Code skill. The deerflow-harness package already implements a comprehensive tool registry that supports built-in tools (bash, read, write, str_replace) and MCP (Model Context Protocol) tools loaded from `extensions_config.json`. The skill's role is to provide visibility into this tool registry through logging and error handling, not to reimplement tool loading.

Key insight: DeerFlowClient already handles all tool orchestration internally. The skill merely needs to:
1. Log which tools are available at startup
2. Provide clear feedback when expected MCP tools are unavailable
3. Not reimplement any tool loading logic (defer to deerflow-harness)

**Primary recommendation:** Add tool logging module that hooks into DeerFlowClient's existing tool registry, with minimal invasive changes to the streaming flow.

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| deerflow-harness | 0.1.0+ | Core agent framework | Provides DeerFlowClient with built-in tool registry |
| langchain-mcp-adapters | 0.1.0+ | MCP tool loading | Required for MCP server tool discovery |
| langchain-core | 0.3.x | Tool abstractions | BaseTool interface for all tools |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.x | Configuration validation | ExtensionsConfig schema validation |
| asyncio | stdlib | Async tool initialization | MCP tool async loading |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Custom tool registry | deerflow.tools.get_available_tools | deerflow-harness already provides complete solution |

**Installation:**
```bash
pip install deerflow-harness langchain-mcp-adapters
```

## Architecture Patterns

### Recommended Project Structure
```
lib/
├── config.py          # Config resolution (Phase 1)
├── errors.py          # Error formatting (Phase 2)
├── modes.py           # Mode presets (Phase 1)
├── stream.py          # Stream handling (Phase 2)
└── tools.py           # Tool logging (Phase 3) - NEW
```

### Pattern 1: Tool Registry Access (Read-Only)
**What:** Access deerflow-harness's existing tool registry for logging purposes
**When to use:** When needing to show which tools are loaded
**Example:**
```python
# Source: deerflow/tools/tools.py
from deerflow.tools import get_available_tools
from deerflow.mcp import get_cached_mcp_tools

def log_available_tools(model_name: str | None = None, subagent_enabled: bool = False) -> None:
    """Log available tools at startup (TOOL-04).
    
    Reads from deerflow-harness tool registry - does NOT load tools itself.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Get built-in and config tools
    all_tools = get_available_tools(
        model_name=model_name,
        subagent_enabled=subagent_enabled
    )
    
    # Get cached MCP tools
    mcp_tools = get_cached_mcp_tools()
    
    logger.info(f"Tools loaded: {len(all_tools)} total")
    logger.info(f"  - MCP tools: {len(mcp_tools)}")
    logger.info(f"  - Built-in tools: {len(all_tools) - len(mcp_tools)}")
    
    for tool in all_tools:
        source = "MCP" if tool in mcp_tools else "builtin"
        logger.info(f"  [{source}] {tool.name}")
```

### Pattern 2: MCP Tool Status Logging
**What:** Log MCP server initialization status on skill startup
**When to use:** TOOL-04 requirement - clear MCP tool loading log
**Example:**
```python
# Source: deerflow/mcp/cache.py, deerflow/mcp/tools.py
from deerflow.config.extensions_config import ExtensionsConfig
from deerflow.mcp.cache import get_cached_mcp_tools

def log_mcp_status() -> None:
    """Log MCP server connection status (TOOL-04)."""
    import logging
    logger = logging.getLogger(__name__)
    
    extensions_config = ExtensionsConfig.from_file()
    enabled_servers = extensions_config.get_enabled_mcp_servers()
    
    if not enabled_servers:
        logger.info("No MCP servers configured")
        return
    
    logger.info(f"Configured MCP servers: {len(enabled_servers)}")
    for name, config in enabled_servers.items():
        transport = config.type or "stdio"
        status = "enabled" if config.enabled else "disabled"
        logger.info(f"  - {name} ({transport}): {status}")
    
    # Log loaded tools
    mcp_tools = get_cached_mcp_tools()
    if mcp_tools:
        logger.info(f"MCP tools loaded: {len(mcp_tools)}")
        for tool in mcp_tools:
            # Tool names are prefixed with server name (e.g., "mcp__server__tool")
            logger.info(f"  - {tool.name}")
```

### Pattern 3: MCP Tool Unavailability Warning
**What:** Warn when expected MCP tools fail to load
**When to use:** TOOL-05 requirement - warn on unavailable MCP tools
**Example:**
```python
# Source: deerflow/config/extensions_config.py
from deerflow.config.extensions_config import ExtensionsConfig
from deerflow.mcp.cache import get_cached_mcp_tools

def check_mcp_tool_availability() -> list[str]:
    """Check for expected but unavailable MCP tools (TOOL-05).
    
    Returns:
        List of warning messages for unavailable tools.
    """
    import logging
    logger = logging.getLogger(__name__)
    warnings = []
    
    extensions_config = ExtensionsConfig.from_file()
    enabled_servers = extensions_config.get_enabled_mcp_servers()
    
    if not enabled_servers:
        return warnings
    
    mcp_tools = get_cached_mcp_tools()
    loaded_tool_names = {t.name for t in mcp_tools}
    
    # Check if any enabled server has no tools loaded
    for server_name, config in enabled_servers.items():
        # Count tools from this server (prefix pattern: mcp__{server}__)
        server_tools = [t for t in mcp_tools if t.name.startswith(f"{server_name}__")]
        
        if not server_tools:
            msg = f"MCP server '{server_name}' enabled but no tools loaded - check server logs"
            warnings.append(msg)
            logger.warning(msg)
    
    return warnings
```

### Anti-Patterns to Avoid
- **Don't load tools directly:** DeerFlowClient handles tool loading internally during `_ensure_agent()`. The skill should only read the registry for logging.
- **Don't reimplement tool deduplication:** deerflow-harness already deduplicates by tool name (see `get_available_tools()`).
- **Don't create custom tool classes:** Use deerflow-harness's built-in tools only.

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Tool loading | Custom tool loader | `get_available_tools()` from deerflow.tools | Handles all built-in tools, subagent tools, MCP tools |
| MCP tool discovery | Custom MCP client | `get_cached_mcp_tools()` from deerflow.mcp | Uses langchain-mcp-adapters, handles async/sync conversion |
| Tool deduplication | Manual name filtering | deerflow's built-in dedup | Already implemented in get_available_tools() |
| MCP config parsing | Custom JSON loader | `ExtensionsConfig.from_file()` | Handles env var expansion, validation |
| Status logging | Custom log formatter | Python logging module | Standard logging with severity levels |

**Key insight:** Tool loading and registry management is completely handled by deerflow-harness. The skill's responsibility is limited to observability (logging) and user feedback (warnings).

## Common Pitfalls

### Pitfall 1: Premature Tool Loading
**What goes wrong:** Calling `get_available_tools()` before DeerFlowClient initializes may load tools with wrong configuration
**Why it happens:** Not understanding that DeerFlowClient's `_ensure_agent()` initializes tools with proper config context
**How to avoid:** Call tool logging functions AFTER DeerFlowClient is created, or use `get_cached_mcp_tools()` which handles lazy initialization
**Warning signs:** Tools loaded without proper model config, MCP tools missing when expected

### Pitfall 2: Ignoring MCP Cache State
**What goes wrong:** Assuming MCP tools are immediately available without checking cache initialization
**Why it happens:** MCP tool loading is async and may not complete before first skill invocation
**How to avoid:** Use `get_cached_mcp_tools()` which handles lazy initialization and returns empty list if not ready
**Warning signs:** Empty MCP tool list when server is configured and enabled

### Pitfall 3: Incorrect MCP Tool Name Matching
**What goes wrong:** Expecting MCP tool names to match exactly instead of being prefixed
**Why it happens:** langchain-mcp-adapters prefixes tool names with server name (e.g., "mcp__filesystem__read")
**How to avoid:** Use prefix matching when checking for tools from specific server: `tool.name.startswith(f"{server_name}__")`
**Warning signs:** False negatives when checking tool availability

## Code Examples

Verified patterns from deerflow-harness source:

### Get All Available Tools
```python
# Source: deerflow/tools/tools.py:35-168
from deerflow.tools import get_available_tools

# Get tools for specific model and mode
tools = get_available_tools(
    model_name="gpt-4",
    subagent_enabled=False
)

for tool in tools:
    print(f"{tool.name}: {tool.description[:50]}...")
```

### Get MCP Tools from Cache
```python
# Source: deerflow/mcp/cache.py:82-130
from deerflow.mcp.cache import get_cached_mcp_tools

# Handles lazy initialization automatically
mcp_tools = get_cached_mcp_tools()

print(f"Loaded {len(mcp_tools)} MCP tools")
for tool in mcp_tools:
    print(f"  - {tool.name}")
```

### Load Extensions Configuration
```python
# Source: deerflow/config/extensions_config.py:118-143
from deerflow.config.extensions_config import ExtensionsConfig

# Load from default location or env var
config = ExtensionsConfig.from_file()

# Get enabled MCP servers
enabled_servers = config.get_enabled_mcp_servers()
for name, server_config in enabled_servers.items():
    print(f"{name}: {server_config.type} @ {server_config.url or 'stdio'}")
```

### Check Tool Name Prefixes
```python
# Source: deerflow/tools/tools.py - deduplication pattern
def get_tools_from_server(mcp_tools: list, server_name: str) -> list:
    """Get tools belonging to a specific MCP server."""
    # MCP tools are prefixed: "{server_name}__{tool_name}"
    prefix = f"{server_name}__"
    return [t for t in mcp_tools if t.name.startswith(prefix)]
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Manual tool loading in skill | DeerFlowClient handles all tool loading | Phase 1 | Skill code simpler, no tool management |
| MCP tools loaded synchronously | Lazy async initialization with cache | deerflow-harness | Non-blocking startup, tools load in background |
| Tool names unprefixed | MCP tools prefixed with server name | langchain-mcp-adapters | Clear tool provenance, name collision avoidance |

**Deprecated/outdated:**
- Direct `MultiServerMCPClient` instantiation: Use `get_cached_mcp_tools()` instead
- Manual tool name matching: Use prefix matching for MCP tools

## Open Questions

1. **When should tool logging occur?**
   - What we know: DeerFlowClient defers agent creation until first call
   - What's unclear: Whether logging should happen at client creation or first stream call
   - Recommendation: Log at first stream invocation, after `_ensure_agent()` completes

2. **How to handle MCP tool loading failures gracefully?**
   - What we know: MCP cache handles exceptions and returns empty list on failure
   - What's unclear: Whether skill should retry or just warn
   - Recommendation: Warn once at startup, let deerflow-harness handle retries

3. **Should skill expose tool list via CLI flag?**
   - What we know: Not in current requirements
   - What's unclear: Future user demand for tool introspection
   - Recommendation: Defer to v2, focus on logging per TOOL-04

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
| TOOL-01 | Skill exposes built-in tools (bash, read, write, str_replace) | integration | `pytest tests/test_tools.py::test_builtin_tools_available -x` | ❌ Wave 0 |
| TOOL-02 | Skill loads MCP tools from extensions_config.json | integration | `pytest tests/test_tools.py::test_mcp_tools_loaded -x` | ❌ Wave 0 |
| TOOL-03 | Tool deduplication by name | unit | `pytest tests/test_tools.py::test_tool_deduplication -x` | ❌ Wave 0 |
| TOOL-04 | MCP tool initialization logging | unit | `pytest tests/test_tools.py::test_mcp_logging -x` | ❌ Wave 0 |
| TOOL-05 | Warn on unavailable MCP tools | unit | `pytest tests/test_tools.py::test_mcp_unavailable_warning -x` | ❌ Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v --cov=lib --cov-report=term-missing`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_tools.py` — covers TOOL-01 through TOOL-05
- [ ] `tests/conftest.py` — mock tools fixtures (extend existing)
- [ ] Mock deerflow.tools module for unit testing without deerflow-harness

*(If no gaps: "None — existing test infrastructure covers all phase requirements")*

## Sources

### Primary (HIGH confidence)
- deerflow/tools/tools.py — tool registry implementation, `get_available_tools()`
- deerflow/mcp/cache.py — MCP tool caching, `get_cached_mcp_tools()`
- deerflow/mcp/tools.py — MCP tool loading via langchain-mcp-adapters
- deerflow/config/extensions_config.py — ExtensionsConfig schema and loading
- deerflow/client.py — DeerFlowClient, `_get_tools()`, `_ensure_agent()`

### Secondary (MEDIUM confidence)
- deerflow/tools/builtins/__init__.py — Built-in tool exports
- deerflow/sandbox/tools.py — Bash, read, write, str_replace implementations

### Tertiary (LOW confidence)
- None - all research based on source code review

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH — directly reviewed deerflow-harness source code
- Architecture: HIGH — deerflow-harness provides complete tool registry
- Pitfalls: MEDIUM — derived from code review, not runtime testing

**Research date:** 2026-04-27
**Valid until:** 90 days — stable APIs in deerflow-harness

---

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| TOOL-01 | Skill exposes deer-flow's built-in tools (bash, read, write, str_replace) | deerflow.tools.get_available_tools() returns all configured tools including built-ins |
| TOOL-02 | Skill loads MCP tools from extensions_config.json | deerflow.mcp.cache.get_cached_mcp_tools() loads from ExtensionsConfig |
| TOOL-03 | Skill deduplicates tools by name across sources | deerflow.tools.tools.py implements dedup in get_available_tools() lines 156-168 |
| TOOL-04 | Skill logs MCP tool initialization status clearly | Logging pattern in deerflow/mcp/cache.py, deerflow/mcp/tools.py |
| TOOL-05 | Skill warns when expected MCP tools are unavailable | Check enabled servers vs loaded tools, warn on mismatch |
</phase_requirements>
