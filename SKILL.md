---
name: deer-flow
description: "Invoke deer-flow agent orchestration directly in Claude Code. Use for complex tasks requiring multi-step reasoning, tool orchestration, or subagent delegation. Supports mode presets: --flash (fastest), --standard (default), --pro (with planning), --ultra (with subagents)."
---

# DeerFlow Skill

## Overview

Invoke the deer-flow agent system directly within Claude Code. No server required - runs embedded in the current process.

This skill imports `deerflow-harness` package directly, leveraging proven agent orchestration without the overhead of a separate server or web interface.

## Usage

```
/deer-flow "your prompt here"
/deer-flow --flash "quick task"
/deer-flow --standard "normal task with reasoning"
/deer-flow --pro "complex task requiring planning"
/deer-flow --ultra "task requiring parallel subagent delegation"
```

### Mode Presets

| Mode | Thinking | Planning | Subagents | Use Case |
|------|----------|----------|-----------|----------|
| `--flash` | No | No | No | Quick tasks, fast responses |
| `--standard` | Yes | No | No | Default, balanced speed and quality |
| `--pro` | Yes | Yes | No | Complex tasks requiring structured planning |
| `--ultra` | Yes | Yes | Yes | Tasks benefiting from parallel agent delegation |

## Configuration

Requires `config.yaml` with model credentials. The skill will auto-create `config.example.yaml` template if missing.

**Config resolution order:**
1. `DEER_FLOW_CONFIG_PATH` environment variable
2. `./config.yaml` (current directory)
3. `../config.yaml` (parent directory)

**Example config.yaml:**
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

## Installation

```bash
# Install via pip
pip install deerflow-harness

# Or with uv
uv add deerflow-harness
```
