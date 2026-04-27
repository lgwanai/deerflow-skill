# Requirements: DeerFlow CLI Skill

**Defined:** 2026-04-27
**Core Value:** Enable Claude Code users to leverage deer-flow's production-grade agent orchestration in their local development workflow with minimal setup.

## v1 Requirements

Requirements for initial release. Each maps to roadmap phases.

### Core Integration

- [x] **CORE-01**: Skill imports deerflow-harness package successfully
- [x] **CORE-02**: Skill validates config.yaml exists and is parseable at initialization
- [x] **CORE-03**: Skill validates required credentials are present in config
- [x] **CORE-04**: Skill creates DeerFlowClient instance with loaded configuration
- [x] **CORE-05**: Skill invokes agent and receives response for single user message

### Configuration

- [x] **CONF-01**: Skill resolves config.yaml path via DEER_FLOW_CONFIG_PATH or default locations
- [x] **CONF-02**: Skill supports environment variable expansion in config values
- [x] **CONF-03**: Skill provides actionable error message when config.yaml missing
- [x] **CONF-04**: Skill provides actionable error message when deerflow-harness not importable

### Tool Calling

- [x] **TOOL-01**: Skill exposes deer-flow's built-in tools (bash, read, write, str_replace)
- [x] **TOOL-02**: Skill loads MCP tools from extensions_config.json
- [ ] **TOOL-03**: Skill deduplicates tools by name across sources
- [x] **TOOL-04**: Skill logs MCP tool initialization status clearly
- [x] **TOOL-05**: Skill warns when expected MCP tools are unavailable

### Streaming

- [x] **STRM-01**: Skill streams agent responses token-by-token
- [x] **STRM-02**: Skill handles LangGraph stream events (values, messages-tuple)
- [x] **STRM-03**: Skill reports tool execution progress during streaming
- [x] **STRM-04**: Skill handles streaming errors gracefully without crashing

### Multi-Provider LLM

- [x] **LLM-01**: Skill supports OpenAI models via config.yaml model.use
- [x] **LLM-02**: Skill supports Anthropic models via config.yaml model.use
- [x] **LLM-03**: Skill supports local models (Ollama) via config.yaml model.use
- [x] **LLM-04**: Skill reports clear error when model credentials missing

### Subagent Delegation

- [x] **SUBA-01**: Skill enables task_tool for subagent delegation
- [x] **SUBA-02**: Skill configures subagent timeout with clear default (900s)
- [x] **SUBA-03**: Skill reports which subagent timed out on timeout error
- [x] **SUBA-04**: Skill exposes MAX_CONCURRENT_SUBAGENTS limit

### Error Handling

- [x] **ERRR-01**: Skill catches recursion limit exceeded with clear message
- [x] **ERRR-02**: Skill catches tool execution errors and continues run
- [x] **ERRR-03**: Skill catches LLM provider errors with actionable message
- [x] **ERRR-04**: Skill documents stateless behavior (no checkpointer by default)

## v2 Requirements

Deferred to future release. Tracked but not in current roadmap.

### Plan Mode

- **PLAN-01**: Skill enables TodoMiddleware for task tracking
- **PLAN-02**: Skill exposes write_todos tool for plan management
- **PLAN-03**: Skill displays todo progress during execution

### Clarification

- **CLAR-01**: Skill enables ClarificationMiddleware for user questions
- **CLAR-02**: Skill handles ask_clarification tool interrupts
- **CLAR-03**: Skill presents clarification prompts to user

### Memory

- **MEMO-01**: Skill optionally enables sqlite checkpointer for multi-turn
- **MEMO-02**: Skill provides memory persistence configuration option
- **MEMO-03**: Skill documents memory storage location

## Out of Scope

Explicitly excluded. Documented to prevent scope creep.

| Feature | Reason |
|---------|--------|
| Frontend/Web UI | Skill is CLI-only, no graphical interface |
| IM channels | No Feishu, Slack, Telegram integration |
| Server mode | No LangGraph server, no Gateway API - embedded only |
| Sandbox isolation | Tools run directly in Claude Code's environment |
| Thread storage | Stateless by design, each invocation is independent |
| Memory extraction | High complexity, defer to v2+ |
| Dynamic tool discovery | Premature optimization, defer until user demand |
| Custom middleware injection | Advanced extensibility, defer to v2+ |

## Traceability

Which phases cover which requirements. Updated during roadmap creation.

| Requirement | Phase | Status |
|-------------|-------|--------|
| CORE-01 | Phase 1 | Complete |
| CORE-02 | Phase 1 | Complete |
| CORE-03 | Phase 1 | Complete |
| CORE-04 | Phase 1 | Complete |
| CORE-05 | Phase 1 | Complete |
| CONF-01 | Phase 1 | Complete |
| CONF-02 | Phase 1 | Complete |
| CONF-03 | Phase 1 | Complete |
| CONF-04 | Phase 1 | Complete |
| TOOL-01 | Phase 3 | Complete |
| TOOL-02 | Phase 3 | Complete |
| TOOL-03 | Phase 3 | Pending |
| TOOL-04 | Phase 3 | Complete |
| TOOL-05 | Phase 3 | Complete |
| STRM-01 | Phase 2 | Complete |
| STRM-02 | Phase 2 | Complete |
| STRM-03 | Phase 2 | Complete |
| STRM-04 | Phase 2 | Complete |
| LLM-01 | Phase 1 | Complete |
| LLM-02 | Phase 1 | Complete |
| LLM-03 | Phase 1 | Complete |
| LLM-04 | Phase 1 | Complete |
| SUBA-01 | Phase 4 | Complete |
| SUBA-02 | Phase 4 | Complete |
| SUBA-03 | Phase 4 | Complete |
| SUBA-04 | Phase 4 | Complete |
| ERRR-01 | Phase 2 | Complete |
| ERRR-02 | Phase 2 | Complete |
| ERRR-03 | Phase 2 | Complete |
| ERRR-04 | Phase 2 | Complete |

**Coverage:**
- v1 requirements: 30 total
- Mapped to phases: 30
- Unmapped: 0 ✓

---
*Requirements defined: 2026-04-27*
*Last updated: 2026-04-27 after initial definition*