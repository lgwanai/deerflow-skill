# Phase 1: Core Integration - Context

**Gathered:** 2026-04-27
**Status:** Ready for planning

<domain>
## Phase Boundary

Establish minimal working skill that imports deerflow-harness, loads config, and invokes the agent. The skill runs embedded (no server), uses deer-flow's config.yaml for configuration, and provides clear error messages for common failure modes. Streaming, MCP tools, and subagent delegation are separate phases.

</domain>

<decisions>
## Implementation Decisions

### Skill Invocation

- **Command format**: `/deer-flow "your prompt here"` - prompt taken as argument
- **Thread ID**: Auto-generate UUID for each call (stateless by design)
- **Model override**: No model override flag - use config.yaml default (first model entry)
- **Mode presets**: Named presets with flags:
  - `--flash`: thinking=false, plan_mode=false, subagent=false (fastest)
  - `--standard`: thinking=true, plan_mode=false, subagent=false (default)
  - `--pro`: thinking=true, plan_mode=true, subagent=false
  - `--ultra`: thinking=true, plan_mode=true, subagent=true
- **Default mode**: Standard (balanced speed and quality)
- **Output**: Print response to stdout, let Claude Code handle display

### Config Resolution

- **config.yaml path**: Check in order:
  1. `DEER_FLOW_CONFIG_PATH` environment variable
  2. `./config.yaml` (current directory)
  3. `../config.yaml` (parent directory)
- **Missing config.yaml**: Auto-create `config.example.yaml` template with example model configs
- **extensions_config.json**: Look alongside config.yaml (same directory)
- **Missing credentials**: Show full guidance:
  - List missing env var names (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`)
  - Show example values
  - Explain where to set them (config.yaml with `$VAR` syntax or shell env)

### Skill Structure

- **Core files**: `SKILL.md`, `skill.py`, `scripts/`, `lib/`, `tests/`, `README.md`, `pyproject.toml`
- **Python modules in lib/**:
  - `config.py` - config path resolution, validation
  - `errors.py` - error message templates and formatting
  - `modes.py` - mode preset definitions and DeerFlowClient config mapping
- **Entry point**: `if __name__ == '__main__'` pattern in skill.py
- **Dependency declaration**: `pyproject.toml` with deerflow-harness as main dependency
- **Scripts**: `scripts/chat.sh` wrapper for quick shell usage
- **Tests**: `tests/` directory with unit tests for config resolution, error formatting, mode mapping

### Error Messages

- **deerflow-harness not importable**: Show install commands:
  ```
  deerflow-harness is not installed. Install with:
    pip install deerflow-harness
  or:
    uv add deerflow-harness
  ```
- **config.yaml parse error**: Show example content in error message AND create `config.example.yaml` template file
- **Missing credentials**: Full guidance format:
  ```
  Missing required credentials:
    OPENAI_API_KEY - Set in config.yaml as: api_key: "$OPENAI_API_KEY"
    ANTHROPIC_API_KEY - Set in config.yaml as: api_key: "$ANTHROPIC_API_KEY"
  
  Example config.yaml:
    models:
      - name: gpt-4
        use: langchain_openai:ChatOpenAI
        api_key: "$OPENAI_API_KEY"
  
  Or set in shell:
    export OPENAI_API_KEY=sk-...
  ```
- **LLM provider errors**: Pass through raw error message (no wrapping)

### Claude's Discretion

- Exact error message wording and formatting
- `config.example.yaml` template content details
- Test coverage granularity
- README.md structure and example content

</decisions>

<specifics>
## Specific Ideas

- "I want users to be able to run deer-flow agent directly in Claude Code without setting up a server"
- Mode presets should match deer-flow's standard mode naming (flash, standard, pro, ultra)
- Skill should feel like a natural extension of Claude Code, not a separate tool

</specifics>

<code_context>
## Existing Code Insights

### Reusable Assets

- `DeerFlowClient` (`deerflow.client`): Complete embedded agent API - use `stream()` for token-by-token output, `chat()` for simple one-shot, `list_models()` for model info
- `get_app_config()` (`deerflow.config.app_config`): Config loading with env var expansion and path resolution - already handles DEER_FLOW_CONFIG_PATH
- `get_extensions_config()` (`deerflow.config.extensions_config`): MCP/skills config loading

### Established Patterns

- SKILL.md format: YAML frontmatter (`name`, `description`) + Markdown instructions (see `skills/public/deep-research/SKILL.md`)
- `if __name__ == '__main__'` entry point pattern (standard Python CLI)
- Config path resolution: `AppConfig.from_file()` already implements priority chain

### Integration Points

- Skill imports `DeerFlowClient` directly: `from deerflow.client import DeerFlowClient`
- Skill calls `client = DeerFlowClient(config_path=resolved_path)`
- Skill calls `response = client.chat(message, thinking_enabled=True, ...)` or streams via `client.stream()`
- No HTTP, no server, no sandbox - pure embedded Python

</code_context>

<deferred>
## Deferred Ideas

- Streaming support (Phase 2)
- MCP tool logging and status (Phase 3)
- Subagent delegation (Phase 4)
- Thread persistence/memory (v2+)

None of these affect Phase 1 - core integration focuses on basic invocation only.

</deferred>

---

*Phase: 01-core-integration*
*Context gathered: 2026-04-27*