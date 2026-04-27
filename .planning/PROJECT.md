# DeerFlow CLI Skill

## What This Is

A Claude Code skill that embeds deer-flow's agent orchestration capabilities directly into Claude Code sessions. Users can invoke deer-flow's powerful agent features (tool calling, subagent delegation, MCP integration) without running a separate server or web interface.

The skill imports `deerflow-harness` package directly and runs an embedded agent loop inside Claude Code, configured via deer-flow's existing `config.yaml`.

## Core Value

Enable Claude Code users to leverage deer-flow's production-grade agent orchestration in their local development workflow with minimal setup.

## Requirements

### Validated

(None yet — ship to validate)

### Active

- [ ] Skill imports and initializes deerflow-harness package
- [ ] Skill runs embedded agent session in Claude Code context
- [ ] Skill exposes deer-flow's tool registry (built-in + MCP tools)
- [ ] Skill supports subagent delegation via task tool
- [ ] Skill reads configuration from deer-flow's config.yaml
- [ ] Skill supports multi-provider LLM (OpenAI, Anthropic, local)
- [ ] Skill provides clear error messages for missing config/dependencies

### Out of Scope

- Frontend/web UI — skill is CLI-only, no graphical interface
- IM channels — no Feishu, Slack, Telegram integration
- Server mode — no LangGraph server, no Gateway API
- Memory system — no thread persistence, no memory extraction
- Sandbox isolation — tools run directly in Claude Code's environment
- Thread management — no thread storage, each invocation is stateless

## Context

DeerFlow is a LangGraph-based AI super agent system with:
- Backend: Agent orchestration, sandbox execution, subagent delegation, MCP integration
- Frontend: Next.js web interface
- Published package: `deerflow-harness` (the core agent framework)

The skill extracts the essential agent functionality into a minimal Claude Code skill format, making deer-flow's capabilities accessible without the full-stack deployment.

**Source project**: ~/project/deer-flow/

## Constraints

- **Package dependency**: Requires `deerflow-harness` package to be importable
- **Configuration**: Requires valid `config.yaml` with model credentials
- **Python runtime**: Skill executes Python code for agent orchestration
- **Claude Code integration**: Must follow skill format conventions

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| Import deerflow-harness directly | Reuse proven code, avoid duplication | — Pending |
| No sandbox isolation | Simpler integration with Claude Code's environment | — Pending |
| Use deer-flow config.yaml | Leverage existing configuration system | — Pending |
| Full tool set exposure | Maximum flexibility for users | — Pending |

---
*Last updated: 2026-04-27 after initialization*
