# Stack Research

**Domain:** Claude Code skill with embedded agent orchestration
**Researched:** 2026-04-27
**Confidence:** HIGH (primary source: deer-flow codebase)

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| Python | 3.12+ | Runtime | deerflow-harness requires `>=3.12`. Matches upstream project constraint. |
| deerflow-harness | 0.1.0 (workspace) | Agent framework | Core package providing `DeerFlowClient`, agent orchestration, tool registry, MCP integration. Direct import eliminates HTTP overhead. |
| LangGraph | 1.0.6-1.0.10 | Agent runtime | Powers deer-flow's agent loop, state management, tool calling. Industry standard for structured agent workflows. |
| LangChain | 1.2.3+ | LLM abstraction | Multi-provider support (OpenAI, Anthropic, local) via unified interface. Mature ecosystem. |
| Pydantic | 2.12.5+ | Configuration | deer-flow config system is Pydantic-based. Skill inherits `config.yaml` parsing for free. |
| PyYAML | 6.0.3+ | Config file | Required for reading deer-flow's `config.yaml`. Standard YAML parsing. |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langchain-openai | 1.1.7+ | OpenAI/OpenAI-compatible models | Default for most LLM providers. Includes OpenRouter, vLLM, local endpoints. |
| langchain-anthropic | 1.3.4+ | Claude models | When using Anthropic API directly. Supports thinking mode. |
| langchain-mcp-adapters | 0.1.0+ | MCP tool integration | Required for MCP server tool exposure. Core to deer-flow's tool registry. |
| langgraph-checkpoint-sqlite | 3.0.3+ | State persistence | For multi-turn conversation support. Optional but recommended. |
| agent-client-protocol | 0.4.0+ | ACP agent integration | For delegating to Codex/Claude Code as subagents. Optional. |
| python-dotenv | 1.0.0+ | Environment variables | For loading `.env` with API keys. Standard practice. |
| tiktoken | 0.8.0+ | Token counting | Used by deer-flow for context management. Good for debugging. |
| ddgs | 9.10.0+ | DuckDuckGo search | Default web search provider. No API key required. |
| tavily-python | 0.7.17+ | Tavily search | Alternative web search with better quality. Requires API key. |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| uv | Package manager | deer-flow uses uv workspace. Fast, modern Python package manager. |
| pytest | Testing | Standard test framework. deer-flow uses pytest-asyncio for async tests. |
| ruff | Linting | deer-flow standard. Fast linter/formatter. |

## Installation

```bash
# Core: Install deerflow-harness and dependencies
# Option 1: From local workspace (recommended for development)
cd /path/to/deer-flow/backend
uv sync

# Option 2: Pass-through dependency in skill's pyproject.toml
# dependencies = ["deerflow-harness"]

# Dev dependencies
uv add --dev pytest pytest-asyncio ruff
```

## Package Structure for Skill

```
deerflow-skill/
├── SKILL.md                    # Claude Code skill definition (frontmatter + instructions)
├── skill.py                    # Python entry point: imports deerflow.client
├── pyproject.toml              # Dependencies (deerflow-harness as requirement)
└── .python-version             # Pin Python 3.12+
```

**SKILL.md Frontmatter Schema (derived from deer-flow skills):**

```yaml
---
name: deerflow-agent
description: "Trigger-based description for Claude Code to match user intent"
---
```

**Entry Point Pattern (skill.py):**

```python
from deerflow.client import DeerFlowClient

def run_agent(prompt: str, thread_id: str | None = None, **kwargs) -> str:
    """Run deer-flow agent with embedded client."""
    client = DeerFlowClient()  # Loads config.yaml automatically
    return client.chat(prompt, thread_id=thread_id, **kwargs)

def stream_agent(prompt: str, thread_id: str | None = None, **kwargs):
    """Stream agent response with events."""
    client = DeerFlowClient()
    for event in client.stream(prompt, thread_id=thread_id, **kwargs):
        yield event
```

## Alternatives Considered

| Recommended | Alternative | When to Use Alternative |
|-------------|-------------|-------------------------|
| deerflow-harness (embedded) | DeerFlow HTTP API | When you need process isolation, remote deployment, or don't want Python dependency |
| LangGraph | CrewAI / AutoGen | When you need multi-agent orchestration with different paradigms (but deer-flow already uses LangGraph internally) |
| Config-driven tools | Hardcoded tools | When you have a fixed, simple toolset (deer-flow's modular approach is overkill for trivial cases) |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| Running deer-flow server | Unnecessary overhead. HTTP adds latency. Skill runs in same process as Claude Code. | Import `DeerFlowClient` directly |
| LangChain Agent (legacy) | deer-flow uses LangGraph's modern agent loop with middleware. Legacy `AgentExecutor` is deprecated. | Use `DeerFlowClient` which wraps LangGraph |
| Custom config parsing | deer-flow has mature Pydantic config system with env var expansion, validation, defaults. | Leverage `config.yaml` via `get_app_config()` |
| Separate tool registration | deer-flow's `get_available_tools()` handles config, MCP, builtins, deduplication. | Call the existing function |

## Integration Patterns

### Pattern 1: Embedded Agent Session

**What:** Run deer-flow agent in Claude Code's Python process
**When:** Primary use case (no server, no sandbox)
**Example:**
```python
from deerflow.client import DeerFlowClient

client = DeerFlowClient(
    config_path="~/.deer-flow/config.yaml",  # Optional, uses defaults
    thinking_enabled=True,
    subagent_enabled=True,
)

# One-shot chat
response = client.chat("Analyze this codebase")

# Streaming (SSE-compatible events)
for event in client.stream("Research quantum computing"):
    if event.type == "messages-tuple":
        print(event.data.get("content", ""), end="")
```

### Pattern 2: Tool Registry Exposure

**What:** Expose deer-flow's tools to Claude Code
**When:** User wants to use individual tools (web_search, file ops, etc.)
**Example:**
```python
from deerflow.tools import get_available_tools
from deerflow.config import get_app_config

# Get tools matching config.yaml
tools = get_available_tools(
    include_mcp=True,           # Include MCP server tools
    model_name="gpt-4o",        # Optional: filter by model
    subagent_enabled=False,     # Exclude task tool for direct use
)

# Tools are LangChain BaseTool instances
for tool in tools:
    print(f"{tool.name}: {tool.description}")
```

### Pattern 3: Subagent Delegation

**What:** Delegate complex tasks to specialized subagents
**When:** Multi-step tasks needing isolated context
**Example:**
```python
client = DeerFlowClient(subagent_enabled=True)

# Task tool is available for delegation
response = client.chat(
    "Create a detailed research report on AI trends",
    thread_id="research-thread",
)
```

### Pattern 4: Multi-Provider LLM

**What:** Support OpenAI, Anthropic, local models via config
**When:** User has different LLM preferences
**Config example:**
```yaml
models:
  - name: gpt-4o
    use: langchain_openai:ChatOpenAI
    model: gpt-4o
    api_key: $OPENAI_API_KEY

  - name: claude-sonnet
    use: langchain_anthropic:ChatAnthropic
    model: claude-sonnet-4-6
    api_key: $ANTHROPIC_API_KEY

  - name: local-llama
    use: langchain_ollama:ChatOllama
    model: llama3.2
    base_url: http://localhost:11434
```

```python
# Override model at runtime
client = DeerFlowClient(model_name="claude-sonnet")
```

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| langgraph@1.0.6-1.0.10 | langchain@1.2.3+ | Pinned range in deerflow-harness |
| langchain-mcp-adapters@0.1.0 | langgraph@1.0.x | MCP tools require this integration |
| deerflow-harness | Python 3.12+ | Uses modern Python features (type hints, pattern matching) |
| langchain-openai | OpenAI API v1 | Compatible with OpenRouter, vLLM, local endpoints via `base_url` |

## Sources

- `/Users/wuliang/project/deer-flow/backend/packages/harness/pyproject.toml` — deerflow-harness dependencies (HIGH confidence)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/client.py` — DeerFlowClient API (HIGH confidence)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/tools/tools.py` — Tool registry (HIGH confidence)
- `/Users/wuliang/project/deer-flow/config.example.yaml` — Configuration schema (HIGH confidence)
- `/Users/wuliang/project/deer-flow/skills/public/deep-research/SKILL.md` — Skill format reference (HIGH confidence)
- `/Users/wuliang/project/deer-flow/skills/public/claude-to-deerflow/SKILL.md` — HTTP API skill reference (HIGH confidence)

---
*Stack research for: Claude Code skill with embedded agent orchestration*
*Researched: 2026-04-27*
