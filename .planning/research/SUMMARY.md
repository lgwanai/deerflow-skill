# Project Research Summary

**Project:** deerflow-skill
**Domain:** Claude Code skill with embedded agent orchestration
**Researched:** 2026-04-27
**Confidence:** HIGH

## Executive Summary

This project builds a Claude Code skill that embeds the deer-flow agent framework directly within Claude Code's process, eliminating the need for a separate server. The skill imports `DeerFlowClient` from the `deerflow-harness` package, leveraging deer-flow's mature LangGraph-based agent orchestration, MCP tool integration, and multi-provider LLM support. This embedded approach is the key differentiator - unlike competitors requiring server deployment, this skill runs entirely within Claude Code's runtime.

The recommended implementation is a thin Python wrapper around `DeerFlowClient`. The skill's primary responsibilities are configuration validation, clear error messaging, and streaming event handling. Core risks include missing or invalid `config.yaml` (the skill depends on deer-flow's configuration system), package importability issues, and recursion limit exhaustion in complex agent loops. These are mitigated through defensive initialization with explicit validation, actionable error messages, and configurable recursion limits.

## Key Findings

### Recommended Stack

The stack centers on `deerflow-harness` as the core dependency, with Python 3.12+ as the runtime requirement. LangGraph powers the agent loop while LangChain provides multi-provider LLM abstraction. The skill itself is minimal - a `SKILL.md` definition plus a thin `skill.py` entry point that delegates to `DeerFlowClient`.

**Core technologies:**
- **Python 3.12+**: Runtime — deerflow-harness requires modern Python features
- **deerflow-harness**: Agent framework — core package providing DeerFlowClient, tool registry, MCP integration
- **LangGraph 1.0.x**: Agent runtime — structured agent workflows with middleware chain
- **LangChain**: LLM abstraction — unified interface for OpenAI, Anthropic, local models
- **Pydantic**: Configuration — deer-flow's config system is Pydantic-based with env var expansion

### Expected Features

**Must have (table stakes):**
- Tool registration and discovery — MCP protocol requirement, users expect to see available tools
- Configuration loading from config.yaml — users need to specify model credentials
- Streaming responses — modern UX expects token-by-token output
- Multi-provider LLM support — users have different model preferences
- Clear error messages — critical for developer experience

**Should have (competitive):**
- Subagent delegation (task_tool) — complex tasks decompose into parallel subtasks, major capability multiplier
- Embedded agent loop (no server) — core differentiator, skill runs entirely in Claude Code process
- Plan mode (TodoMiddleware) — multi-step tasks get tracked, agent stays organized
- Clarification requests — agent can ask questions instead of guessing

**Defer (v2+):**
- Memory persistence — high complexity, requires storage decisions
- Dynamic tool discovery — useful for power users with many MCP tools
- Custom middleware injection — advanced extensibility

### Architecture Approach

The architecture is a thin wrapper pattern: `skill.py` imports `DeerFlowClient` directly, which handles all orchestration (config loading, model creation, tool assembly, middleware chain, agent execution, streaming). No HTTP, no server, no sandbox. The skill's only job is to validate initialization conditions and translate events for Claude Code.

**Major components:**
1. **SKILL.md** — Claude Code skill definition with YAML frontmatter for intent matching
2. **skill.py** — Thin entry point importing DeerFlowClient, no business logic
3. **DeerFlowClient** — Core client orchestrating agent execution via LangGraph
4. **Tool Registry** — Merges config tools + builtins + MCP servers
5. **Middleware Chain** — Memory, Title, TodoList, Clarification middlewares

### Critical Pitfalls

1. **Missing or invalid config.yaml** — Skill must validate config exists and has required credentials at initialization, not lazily on first LLM call. Provide actionable error messages with expected paths.

2. **deerflow-harness not importable** — Wrap import in try/except with clear error message documenting installation (`pip install deerflow-harness` or `uv add deerflow-harness`).

3. **Recursion limit exceeded** — Configure reasonable defaults (`recursion_limit=100`), expose as configurable, log when approaching limits.

4. **MCP tool initialization fails silently** — Log MCP initialization status clearly, warn users when expected tools are unavailable.

5. **Thread state loss without checkpointer** — Document that stateless mode is intentional; if multi-turn is needed, configure sqlite checkpointer.

## Implications for Roadmap

Based on research, suggested phase structure:

### Phase 1: Core Skill Structure
**Rationale:** Establish minimal working skill that can invoke the agent and get a response. Foundation for all other features.
**Delivers:** Runnable Claude Code skill with basic agent invocation
**Addresses:** Configuration loading, tool registry exposure, multi-provider LLM support
**Avoids:** Missing config.yaml silent failure, import errors without guidance

### Phase 2: Streaming and Error Handling
**Rationale:** Modern UX requires streaming; clear errors are critical for developer experience. These must work before adding complexity.
**Delivers:** Streaming responses, actionable error messages for all failure modes
**Uses:** LangGraph stream modes (values, messages-tuple, end events)
**Implements:** StreamEvent handling in skill.py

### Phase 3: MCP Integration
**Rationale:** MCP tools are a key capability. Users expect tools from configured MCP servers to work.
**Delivers:** Full MCP tool exposure, MCP status logging
**Uses:** DeferredToolRegistry pattern, get_cached_mcp_tools()
**Avoids:** MCP initialization silent failure

### Phase 4: Subagent Delegation
**Rationale:** Subagent delegation is the major capability multiplier. Requires stable core to build upon.
**Delivers:** Task tool for parallel subtask execution
**Uses:** DeerFlowClient with subagent_enabled=True, ACP agent integration
**Avoids:** Subagent timeout without clear feedback

### Phase 5: Enhanced Features
**Rationale:** Plan mode and clarification requests improve complex task handling but are not essential for MVP.
**Delivers:** TodoMiddleware for plan tracking, ClarificationMiddleware for user questions
**Uses:** Middleware chain pattern

### Phase Ordering Rationale

- Dependencies flow from core to enhanced: skill structure -> streaming -> MCP -> subagents -> enhancements
- Architecture pattern (thin wrapper) implies minimal code in each phase - most work is configuration and error handling
- Pitfalls are addressed in order of severity: config/import errors (Phase 1) are more catastrophic than recursion limits (Phase 4)

### Research Flags

Phases likely needing deeper research during planning:
- **Phase 3 (MCP Integration):** MCP server connectivity issues can be complex; may need MCP Inspector integration and debugging patterns
- **Phase 4 (Subagent Delegation):** Subagent timeout handling, ACP agent configuration, and parallel execution patterns need validation

Phases with standard patterns (skip research-phase):
- **Phase 1 (Core Skill Structure):** Well-documented patterns from deer-flow skill examples (deep-research, claude-to-deerflow)
- **Phase 2 (Streaming and Error Handling):** Standard LangGraph stream modes, straightforward error message patterns

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | Primary source: deer-flow codebase (pyproject.toml, client.py, tools.py) |
| Features | HIGH | Deer-flow README, existing skill implementations provide comprehensive feature map |
| Architecture | HIGH | Direct codebase analysis of DeerFlowClient, middleware chain, tool registry |
| Pitfalls | MEDIUM | Derived from code analysis and MCP documentation; some runtime behaviors not fully tested |

**Overall confidence:** HIGH

### Gaps to Address

- **Deerflow-harness publish status:** The package may not be published to PyPI; may need local workspace dependency or publishing step. Verify in Phase 1.
- **Claude Code skill invocation mechanism:** Exact pattern for Claude Code invoking Python skills needs verification in SKILL.md format. Test in Phase 1.
- **Subagent behavior under load:** Parallel subagent execution patterns need real-world validation. Address in Phase 4 if issues arise.

## Sources

### Primary (HIGH confidence)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/pyproject.toml` — deerflow-harness dependencies
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/client.py` — DeerFlowClient API
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/tools/tools.py` — Tool registry
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/config/app_config.py` — Config system
- `/Users/wuliang/project/deer-flow/skills/public/deep-research/SKILL.md` — Skill format reference
- [MCP Tools Specification](https://modelcontextprotocol.io/specification/latest/server/tools) — Tool calling protocol

### Secondary (MEDIUM confidence)
- [MCP Debugging Guide](https://modelcontextprotocol.io/docs/tools/debugging) — Common MCP issues and logging strategies
- [Claude Code Skills documentation](https://docs.anthropic.com/en/docs/claude-code/skills) — Skills format

---
*Research completed: 2026-04-27*
*Ready for roadmap: yes*
