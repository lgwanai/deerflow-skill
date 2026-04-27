# Roadmap: DeerFlow CLI Skill

## Overview

Build a Claude Code skill that embeds deer-flow's production-grade agent orchestration directly into Claude Code sessions. The journey starts with core integration (package import, config loading, multi-provider LLM support), adds streaming responses and error handling, exposes the full tool registry including MCP tools, and enables subagent delegation for parallel task execution.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Core Integration** - Establish minimal working skill that imports deerflow-harness, loads config, and invokes the agent
- [ ] **Phase 2: Streaming and Error Handling** - Add token-by-token streaming responses and actionable error messages for all failure modes
- [ ] **Phase 3: Tool Registry Exposure** - Expose built-in tools and MCP tools with clear initialization logging
- [ ] **Phase 4: Subagent Delegation** - Enable task_tool for parallel subtask execution with timeout handling

## Phase Details

### Phase 1: Core Integration
**Goal**: A runnable Claude Code skill that can invoke the deer-flow agent and receive a response
**Depends on**: Nothing (first phase)
**Requirements**: CORE-01, CORE-02, CORE-03, CORE-04, CORE-05, CONF-01, CONF-02, CONF-03, CONF-04, LLM-01, LLM-02, LLM-03, LLM-04
**Success Criteria** (what must be TRUE):
  1. User can invoke the skill and receive a response from the deer-flow agent
  2. User receives clear error when config.yaml is missing or invalid
  3. User receives clear error when deerflow-harness is not installed
  4. User can use any configured LLM provider (OpenAI, Anthropic, Ollama)
  5. User sees actionable error message when model credentials are missing
**Plans**: 3 plans

Plans:
- [x] 01-01-PLAN.md - Core skill structure (SKILL.md, pyproject.toml) and deerflow-harness dependency
- [x] 01-02-PLAN.md - Configuration loading, validation, and actionable error messages
- [x] 01-03-PLAN.md - Mode presets, skill.py entry point, and multi-provider LLM invocation

### Phase 2: Streaming and Error Handling
**Goal**: Modern UX with streaming responses and actionable error messages
**Depends on**: Phase 1
**Requirements**: STRM-01, STRM-02, STRM-03, STRM-04, ERRR-01, ERRR-02, ERRR-03, ERRR-04
**Success Criteria** (what must be TRUE):
  1. User sees agent responses stream token-by-token in real-time
  2. User sees tool execution progress during agent runs
  3. User receives clear message when recursion limit is exceeded
  4. User sees LLM provider errors with actionable guidance
  5. User understands that sessions are stateless (no memory persistence by default)
**Plans**: 2 plans

Plans:
- [ ] 02-01-PLAN.md - Stream event handler with real-time token output and tool progress
- [ ] 02-02-PLAN.md - Error handling wrapper with GraphRecursionError and LLM error guidance

### Phase 3: Tool Registry Exposure
**Goal**: Full tool ecosystem available including MCP tools
**Depends on**: Phase 2
**Requirements**: TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-05
**Success Criteria** (what must be TRUE):
  1. User can use deer-flow's built-in tools (bash, read, write, str_replace)
  2. User can use tools from configured MCP servers
  3. User sees clear log of which MCP tools loaded successfully
  4. User is warned when expected MCP tools are unavailable
**Plans**: TBD

Plans:
- [ ] 03-01-PLAN.md - Built-in tool exposure
- [ ] 03-02-PLAN.md - MCP tool integration and logging

### Phase 4: Subagent Delegation
**Goal**: Complex tasks decompose into parallel subagents
**Depends on**: Phase 3
**Requirements**: SUBA-01, SUBA-02, SUBA-03, SUBA-04
**Success Criteria** (what must be TRUE):
  1. User can delegate tasks to subagents via task_tool
  2. User sees which subagent timed out when timeout occurs
  3. User can configure concurrent subagent limit
  4. Subagent timeout has clear default behavior (900s)
**Plans**: TBD

Plans:
- [ ] 04-01-PLAN.md - Subagent delegation configuration
- [ ] 04-02-PLAN.md - Timeout handling and feedback

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Integration | 3/3 | Complete | 2026-04-27 |
| 2. Streaming and Error Handling | 0/2 | Ready to execute | - |
| 3. Tool Registry Exposure | 0/2 | Not started | - |
| 4. Subagent Delegation | 0/2 | Not started | - |

---
*Roadmap created: 2026-04-27*
*Last updated: 2026-04-27 - Phase 2 plans created*