# DeerFlow CLI Skill

A Claude Code skill that embeds deer-flow's agent orchestration capabilities directly into Claude Code sessions. Invoke deer-flow's powerful agent features without running a separate server or web interface.

## Overview

The skill imports `deerflow-harness` package directly and runs an embedded agent loop inside Claude Code, configured via deer-flow's existing `config.yaml`. This provides:

- Multi-step reasoning with thinking mode
- Tool orchestration and MCP integration
- Subagent delegation for parallel task execution
- Multi-provider LLM support (OpenAI, Anthropic, local)

## Installation

```bash
# Install via pip
pip install deerflow-harness

# Or with uv
uv add deerflow-harness
```

## Quick Start

1. **Create config.yaml** with your model credentials:

```yaml
models:
  - name: gpt-4
    use: langchain_openai:ChatOpenAI
    api_key: "$OPENAI_API_KEY"

  - name: claude-3-sonnet
    use: langchain_anthropic:ChatAnthropic
    api_key: "$ANTHROPIC_API_KEY"

sandbox:
  enabled: false
```

2. **Set environment variables** for API keys:

```bash
export OPENAI_API_KEY=sk-...
export ANTHROPIC_API_KEY=sk-ant-...
```

3. **Invoke the skill** in Claude Code:

```
/deer-flow "analyze the codebase and suggest improvements"
```

## Mode Presets

| Mode | Flag | Thinking | Planning | Subagents | Best For |
|------|------|----------|----------|-----------|----------|
| Flash | `--flash` | No | No | No | Quick responses, simple queries |
| Standard | `--standard` | Yes | No | No | Default mode, balanced quality/speed |
| Pro | `--pro` | Yes | Yes | No | Complex tasks requiring structured planning |
| Ultra | `--ultra` | Yes | Yes | Yes | Parallel subagent delegation |

### Usage Examples

```
# Quick task (fastest)
/deer-flow --flash "list the main components"

# Default reasoning mode
/deer-flow --standard "explain how the auth flow works"

# With planning for complex tasks
/deer-flow --pro "design a new feature for user notifications"

# With subagent delegation for parallel work
/deer-flow --ultra "analyze performance across all modules"
```

## Configuration Reference

### Config File Location

The skill searches for `config.yaml` in this order:

1. `DEER_FLOW_CONFIG_PATH` environment variable (explicit path)
2. `./config.yaml` (current working directory)
3. `../config.yaml` (parent directory)

### Config Structure

```yaml
models:
  - name: <model-name>
    use: <langchain-provider>:<class>
    api_key: "$<ENV_VAR>"  # Environment variable reference
    # Additional model params...

sandbox:
  enabled: false  # No sandbox - runs directly in Claude Code

extensions_config:
  mcp_servers: []  # MCP server configurations (optional)
```

### Supported LLM Providers

| Provider | `use` Field | Required Env Var |
|----------|-------------|------------------|
| OpenAI | `langchain_openai:ChatOpenAI` | `OPENAI_API_KEY` |
| Anthropic | `langchain_anthropic:ChatAnthropic` | `ANTHROPIC_API_KEY` |
| Ollama | `langchain_ollama:ChatOllama` | None (local) |

### Example Configurations

**OpenAI only:**
```yaml
models:
  - name: gpt-4o
    use: langchain_openai:ChatOpenAI
    api_key: "$OPENAI_API_KEY"
    model_name: gpt-4o
```

**Anthropic only:**
```yaml
models:
  - name: claude-3-sonnet
    use: langchain_anthropic:ChatAnthropic
    api_key: "$ANTHROPIC_API_KEY"
    model_name: claude-3-sonnet-20240229
```

**Local Ollama:**
```yaml
models:
  - name: llama3
    use: langchain_ollama:ChatOllama
    model_name: llama3
    base_url: http://localhost:11434
```

## Error Handling

The skill provides clear, actionable error messages:

- **Missing package:** Shows pip/uv install commands
- **Missing config:** Creates `config.example.yaml` template with guidance
- **Missing credentials:** Lists required env vars with example values

## Project Structure

```
deerflow-skill/
├── SKILL.md           # Claude Code skill definition
├── skill.py           # Entry point (future phase)
├── lib/
│   ├── __init__.py    # Package marker
│   ├── config.py      # Config resolution (future phase)
│   ├── errors.py      # Error formatting (future phase)
│   └── modes.py       # Mode presets (future phase)
├── scripts/
│   └── chat.sh        # Shell wrapper (future phase)
├── tests/             # Test suite (future phase)
├── README.md          # This documentation
└── pyproject.toml     # Dependencies
```

## License

MIT

## Links

- **Source:** deer-flow agent framework
- **Package:** deerflow-harness on PyPI