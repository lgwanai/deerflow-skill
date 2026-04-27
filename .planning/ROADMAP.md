# Roadmap: DeerFlow CLI Skill

## Overview

Build a Claude Code skill that embeds deer-flow's production-grade agent orchestration directly into Claude Code sessions. The journey starts with core integration (package import, config loading, multi-provider LLM support), adds streaming responses and error handling, exposes the full tool registry including MCP tools, and enables subagent delegation for parallel task execution.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [ ] **Phase 1: Core Integration** - Establish minimal working skill that imports deerflow-harness, loads config, and invokes the agent
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
**Plans**: TBD

Plans:
- [ ] 01-01: Core skill structure and deerflow-harness integration
- [ ] 01-02: Configuration loading and validation
- [ ] 01-03: Multi-provider LLM support

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
**Plans**: TBD

Plans:
- [ ] 02-01: Streaming response implementation
- [ ] 02-02: Error handling and user messaging

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
- [ ] 03-01: Built-in tool exposure
- [ ] 03-02: MCP tool integration and logging

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
- [ ] 04-01: Subagent delegation configuration
- [ ] 04-02: Timeout handling and feedback

## Progress

**Execution Order:**
Phases execute in numeric order: 1 -> 2 -> 3 -> 4

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Core Integration | 0/3 | Not started | - |
| 2. Streaming and Error Handling | 0/2 | Not started | - |
| 3. Tool Registry Exposure | 0/2 | Not started | - |
| 4. Subagent Delegation | 0/2 | Not started | - |

---
*Roadmap created: 2026-04-27*