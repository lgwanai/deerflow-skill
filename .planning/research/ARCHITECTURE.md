# Architecture Research

**Domain:** Claude Code skill with embedded agent orchestration
**Researched:** 2026-04-27
**Confidence:** HIGH (primary source: deer-flow codebase analysis)

## Standard Architecture

### System Overview

```
+------------------------------------------------------------------+
|                     Claude Code Host Process                      |
+------------------------------------------------------------------+
                                |
                                v
+------------------------------------------------------------------+
|                      DeerFlow Skill (SKILL.md)                    |
|  +------------------------------------------------------------+  |
|  |                    Skill Entry Point                        |  |
|  |                 (skill.py / SKILL.md)                       |  |
|  +----------------------------+-------------------------------+  |
|                               |                                  |
|                               v                                  |
|  +------------------------------------------------------------+  |
|  |                    DeerFlowClient                           |  |
|  |  (deerflow.client.DeerFlowClient)                           |  |
|  |                                                             |  |
|  |  Responsibilities:                                          |  |
|  |  - Load config.yaml                                         |  |
|  |  - Create LLM model instance                                |  |
|  |  - Assemble tool registry (builtins + MCP)                  |  |
|  |  - Build middleware chain                                   |  |
|  |  - Execute agent loop (LangGraph)                           |  |
|  |  - Stream events to caller                                  |  |
|  +----------------------------+-------------------------------+  |
|                               |                                  |
|          +--------------------+--------------------+             |
|          |                    |                    |             |
|          v                    v                    v             |
|  +-------------+      +-------------+      +-------------+       |
|  | LLM Model   |      | Tool        |      | Middleware  |       |
|  | Factory     |      | Registry    |      | Chain       |       |
|  |             |      |             |      |             |       |
|  | - OpenAI    |      | - Builtins  |      | - Memory    |       |
|  | - Anthropic |      | - MCP Tools |      | - Title     |       |
|  | - Local     |      | - Task Tool |      | - TodoList  |       |
|  |             |      |             |      | - Etc.      |       |
|  +-------------+      +-------------+      +-------------+       |
|                               |                                  |
+-------------------------------+----------------------------------+
                                |
                                v
+------------------------------------------------------------------+
|                    External Dependencies                          |
|  +------------------+  +------------------+  +-----------------+  |
|  | config.yaml      |  | MCP Servers      |  | LLM APIs        |  |
|  | (User Config)    |  | (Tool Sources)   |  | (Providers)     |  |
|  +------------------+  +------------------+  +-----------------+  |
+------------------------------------------------------------------+
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **SKILL.md** | Claude Code skill definition with frontmatter + instructions | YAML frontmatter + Markdown body |
| **skill.py** | Python entry point importing DeerFlowClient | Thin wrapper calling `DeerFlowClient.chat()` or `DeerFlowClient.stream()` |
| **DeerFlowClient** | Core client orchestrating agent execution | Embedded agent session with LangGraph runtime |
| **Model Factory** | Create LLM instances from config | `create_chat_model()` resolves provider from `use` field |
| **Tool Registry** | Assemble available tools | `get_available_tools()` merges config tools + builtins + MCP |
| **Middleware Chain** | Process agent state at each step | Memory, Title, TodoList, Clarification middlewares |
| **Config System** | Load and validate config.yaml | Pydantic models with env var expansion |

## Recommended Project Structure

```
deerflow-skill/
+-- SKILL.md                     # Claude Code skill definition (frontmatter + instructions)
+-- skill.py                     # Python entry point (imports deerflow.client)
+-- pyproject.toml               # Dependencies: deerflow-harness, langchain-*
+-- .python-version              # Pin Python 3.12+
+-- scripts/                     # Optional helper scripts
|   +-- check-config.sh          # Verify config.yaml exists and is valid
|   +-- test-skill.py            # Simple test harness
+-- tests/                       # Test suite
    +-- test_skill.py            # Integration tests
```

### Structure Rationale

- **SKILL.md:** Claude Code convention for skill definition. Frontmatter contains name/description for intent matching. Body contains instructions for Claude Code to follow when invoking the skill.
- **skill.py:** Thin entry point. Imports `DeerFlowClient` from `deerflow-harness`. No business logic - delegates to the harness.
- **pyproject.toml:** Declares `deerflow-harness` as dependency. uv syncs from local workspace or published package.
- **No config/:** Uses deer-flow's existing `config.yaml` resolution (user's home or project directory).

## Architectural Patterns

### Pattern 1: Embedded Client Pattern

**What:** Import `DeerFlowClient` directly into skill process instead of HTTP calls to a server.

**When to use:** Primary pattern for this skill. Claude Code skill runs in the same process as the agent framework.

**Trade-offs:**
- (+) Zero HTTP latency, single-process execution
- (+) Direct Python API, no serialization overhead
- (+) Shared config system with deer-flow
- (-) Requires deerflow-harness package to be importable
- (-) No process isolation (tools run in Claude Code's environment)

**Example:**
```python
from deerflow.client import DeerFlowClient

def run_agent(prompt: str, thread_id: str | None = None) -> str:
    """Run deer-flow agent embedded in Claude Code."""
    client = DeerFlowClient(
        thinking_enabled=True,
        subagent_enabled=True,
    )
    return client.chat(prompt, thread_id=thread_id)
```

### Pattern 2: Streaming Event Pattern

**What:** Stream agent response as events (values, messages-tuple, end) instead of blocking until complete.

**When to use:** For long-running tasks, providing incremental feedback to user.

**Trade-offs:**
- (+) User sees progress in real-time
- (+) Can handle long responses without timeout
- (-) More complex event handling logic

**Example:**
```python
from deerflow.client import DeerFlowClient, StreamEvent

def stream_agent(prompt: str) -> None:
    client = DeerFlowClient()
    for event in client.stream(prompt):
        if event.type == "messages-tuple" and event.data.get("type") == "ai":
            print(event.data.get("content", ""), end="", flush=True)
        elif event.type == "end":
            print(f"\n[Done: {event.data['usage']['total_tokens']} tokens]")
```

### Pattern 3: Config-Driven Tool Assembly

**What:** Tools are assembled from config.yaml + MCP servers + builtins, not hardcoded.

**When to use:** Always. This is deer-flow's default behavior via `get_available_tools()`.

**Trade-offs:**
- (+) User controls tool set via config
- (+) MCP tools discovered automatically
- (+) Deduplication by tool name
- (-) Config errors cause missing tools

**Example:**
```python
# Tools are loaded automatically by DeerFlowClient
# User configures in config.yaml:
# tools:
#   - name: web_search
#     use: deerflow.tools.web_search:web_search_tool
#
# MCP servers configured in extensions_config.json
# add automatically to tool registry
```

### Pattern 4: Middleware Chain Pattern

**What:** Agent behavior modified via middleware chain (Memory, Title, TodoList, etc.)

**When to use:** Enable/disable features via config or runtime parameters.

**Trade-offs:**
- (+) Modular feature composition
- (+) Easy to add custom middleware
- (-) Order matters (must match deer-flow conventions)

**Example:**
```python
# Middleware built by _build_middlewares() in deer-flow
# Key middlewares (in order):
# 1. SummarizationMiddleware - context compression
# 2. TodoMiddleware - plan mode support
# 3. TitleMiddleware - auto title generation
# 4. MemoryMiddleware - conversation memory
# 5. LoopDetectionMiddleware - break infinite loops
# 6. ClarificationMiddleware - ask user questions
```

## Data Flow

### Request Flow

```
[Claude Code User Input]
         |
         v
[SKILL.md Intent Match]
         |
         v
[skill.py Entry Point]
         |
         v
[DeerFlowClient.__init__()]
    - load config.yaml
    - resolve model_name
         |
         v
[DeerFlowClient.stream() / .chat()]
    - create HumanMessage
    - build RunnableConfig
    - call _ensure_agent()
         |
         v
[_ensure_agent()]
    - create_chat_model()
    - get_available_tools()
    - _build_middlewares()
    - create_agent()
         |
         v
[agent.stream(state, config)]
    - LangGraph agent loop
    - middleware invoked per step
    - tools called as needed
         |
         v
[StreamEvent emission]
    - "messages-tuple" for AI text deltas
    - "tool" for tool results
    - "values" for state snapshots
    - "end" for completion
         |
         v
[Response to Claude Code]
```

### State Management

```
[ThreadState]
    - messages: list[Message]      # Conversation history
    - title: str | None            # Auto-generated title
    - artifacts: list[Artifact]    # Generated files
         |
         v
[Checkpointer (optional)]
    - SQLite/memory persistence
    - Enables multi-turn context
         |
         v
[Thread ID isolation]
    - Each thread has isolated uploads/
    - Artifacts stored per-thread
```

### Key Data Flows

1. **Config Loading:** `config.yaml` -> `AppConfig.from_file()` -> singleton cached -> `get_app_config()` returns cached instance

2. **Tool Assembly:** `config.tools` + `ExtensionsConfig.mcp_servers` + `BUILTIN_TOOLS` -> `get_available_tools()` -> deduplicated list -> bound to agent

3. **Model Creation:** `config.models[i]` -> `create_chat_model(name)` -> provider class resolved from `use` field (e.g., `langchain_openai:ChatOpenAI`)

4. **Event Streaming:** `agent.stream()` -> LangGraph stream modes -> `StreamEvent` objects -> caller iterates

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| Single user | Default embedded client is optimal. No changes needed. |
| Multiple skills | Each skill creates own `DeerFlowClient` instance. Shared config.yaml. |
| Heavy tool use | Consider increasing `recursion_limit` in config. MCP tools may need connection pooling. |

### Scaling Priorities

1. **First bottleneck:** Tool execution time (especially MCP tools). Mitigation: Use `subagent_enabled=True` for parallel delegation.

2. **Second bottleneck:** Context window exhaustion. Mitigation: `summarization` config auto-compresses old messages.

## Anti-Patterns

### Anti-Pattern 1: Running deer-flow Server

**What people do:** Start deer-flow server and make HTTP calls from the skill.

**Why it's wrong:** Unnecessary overhead. HTTP adds latency, requires separate process management, duplicates what `DeerFlowClient` already provides.

**Do this instead:** Import `DeerFlowClient` directly. No server needed.

```python
# WRONG: HTTP API call
import requests
response = requests.post("http://localhost:2026/api/langgraph/threads/...", ...)

# CORRECT: Embedded client
from deerflow.client import DeerFlowClient
client = DeerFlowClient()
response = client.chat("hello")
```

### Anti-Pattern 2: Hardcoded Tools

**What people do:** Manually construct tool list in skill code.

**Why it's wrong:** Bypasses deer-flow's tool registry, MCP integration, deduplication, and config-driven behavior.

**Do this instead:** Let `DeerFlowClient` load tools from config. Users configure in `config.yaml` and `extensions_config.json`.

```python
# WRONG: Hardcoded tools
tools = [web_search_tool, bash_tool]

# CORRECT: Config-driven (automatic)
client = DeerFlowClient()
# Tools loaded from config.yaml + MCP servers automatically
```

### Anti-Pattern 3: Custom Config Parsing

**What people do:** Parse config.yaml with custom logic.

**Why it's wrong:** Deer-flow has mature Pydantic config system with env var expansion, validation, defaults.

**Do this instead:** Use `get_app_config()` or let `DeerFlowClient` load config automatically.

```python
# WRONG: Custom parsing
import yaml
with open("config.yaml") as f:
    config = yaml.safe_load(f)

# CORRECT: Use deer-flow's config system
from deerflow.config import get_app_config
config = get_app_config()
print(config.models[0].name)
```

### Anti-Pattern 4: Ignoring Statelessness

**What people do:** Assume thread_id provides multi-turn context without checkpointer.

**Why it's wrong:** Without a checkpointer, each `chat()`/`stream()` call is stateless. `thread_id` only isolates file uploads.

**Do this instead:** If multi-turn is needed, configure checkpointer in `config.yaml` under `checkpointer` section.

```python
# Checkpointer configuration in config.yaml:
# checkpointer:
#   provider: sqlite
#   sqlite_path: ~/.deer-flow/checkpoints.db

# Or pass checkpointer explicitly:
from langgraph_checkpoint_sqlite import SqliteSaver
client = DeerFlowClient(checkpointer=SqliteSaver.from_conn_string("checkpoints.db"))
```

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| LLM APIs (OpenAI, Anthropic) | Via `config.yaml` models section | `use` field specifies provider class |
| MCP Servers | Via `extensions_config.json` | Tools discovered at startup |
| Local models (Ollama, vLLM) | Via `base_url` in model config | OpenAI-compatible endpoint |
| ACP Agents (Codex, Claude Code) | Via `acp_agents` config | Subagent delegation |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| skill.py <-> DeerFlowClient | Direct Python call | No serialization |
| DeerFlowClient <-> LangGraph | Agent.stream() | Stream modes: values, messages, custom |
| DeerFlowClient <-> Tools | Tool.invoke() | Tools run in same process |
| DeerFlowClient <-> Config | get_app_config() | Singleton, auto-reload on file change |

## Build Order Implications

Based on the architecture, recommended implementation order:

1. **Phase 1: Core Skill Structure**
   - Create SKILL.md with frontmatter + basic instructions
   - Create skill.py with minimal DeerFlowClient integration
   - Create pyproject.toml with deerflow-harness dependency
   - Test: Can invoke agent and get response

2. **Phase 2: Configuration Integration**
   - Document config.yaml requirements
   - Add config validation error messages
   - Test: Missing config produces helpful error

3. **Phase 3: Streaming Support**
   - Implement streaming in skill.py
   - Handle StreamEvent types
   - Test: Long responses stream incrementally

4. **Phase 4: Tool Exposure**
   - Document tool configuration
   - Test: MCP tools are available
   - Test: Built-in tools work

5. **Phase 5: Subagent Delegation**
   - Enable subagent_enabled=True
   - Test: Task tool can delegate to Codex/Claude Code
   - Configure ACP agents if needed

## Sources

- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/client.py` - DeerFlowClient API (HIGH confidence)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/tools/tools.py` - Tool registry (HIGH confidence)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/models/factory.py` - Model creation (HIGH confidence)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/config/app_config.py` - Config system (HIGH confidence)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/agents/lead_agent/agent.py` - Agent construction (HIGH confidence)
- `/Users/wuliang/project/deer-flow/skills/public/claude-to-deerflow/SKILL.md` - HTTP API skill reference (HIGH confidence)
- `/Users/wuliang/project/deer-flow/skills/public/deep-research/SKILL.md` - Skill format reference (HIGH confidence)

---
*Architecture research for: Claude Code skill with embedded agent orchestration*
*Researched: 2026-04-27*
