---
name: deer
description: >
  DeerFlow agent orchestration. Use for complex tasks requiring multi-step reasoning,
  web search, tool orchestration, or parallel subagent delegation. Triggers: '用deer',
  'deer帮我', '调用deer', 'research task', 'complex query'.
allowed-tools: Bash(python scripts/skill.py:*), Bash(./scripts/chat.sh:*)
---

# DeerFlow Agent

Invoke the DeerFlow agent system directly within Claude Code. No server required - runs embedded in the current process.

## Activation

```
/deer "your prompt here"
/deer --flash "quick task"
/deer --pro "complex task needing planning"
/deer --ultra "task requiring parallel subagent delegation"
```

## Mode Presets

| Mode | Thinking | Planning | Subagents | Use Case |
|------|----------|----------|-----------|----------|
| `--flash` | No | No | No | Quick responses, simple queries |
| `--standard` | Yes | No | No | Default, balanced speed and quality |
| `--pro` | Yes | Yes | No | Complex tasks requiring structured planning |
| `--ultra` | Yes | Yes | Yes | Parallel subagent delegation for heavy workloads |

## Features

- **Web Search**: Search the web for current information via Tavily
- **Web Fetch**: Fetch and extract content from web pages via Jina AI
- **Multi-step Reasoning**: Extended thinking for complex problems
- **Planning Mode**: Structured task decomposition with TodoList
- **Subagent Delegation**: Parallel task execution with specialized agents

## Configuration

Requires `config.yaml` with model credentials. Copy `config.example.yaml` to `config.yaml` and configure:

**Required environment variables:**
- `DEEPSEEK_API_KEY` - DeepSeek API key (recommended, cost-effective)
- `TAVILY_API_KEY` - Tavily API key for web search
- `JINA_API_KEY` - Jina AI API key for web fetch

**Alternative models:**
- `OPENAI_API_KEY` - OpenAI API key
- `ANTHROPIC_API_KEY` - Anthropic API key

## Examples

```
/deer "Research the latest developments in quantum computing"
/deer --flash "What is the capital of France?"
/deer --pro "Create a detailed project plan for building a REST API"
/deer --ultra "Analyze performance across all modules and identify bottlenecks"
```

## Installation

The skill uses its own embedded deerflow modules. Ensure dependencies are installed:

```bash
pip install langchain langchain-anthropic langchain-openai tavily-python httpx
```

## Notes

- First run may be slower as the agent initializes
- Web search and fetch require API keys in config.yaml
- For local models via Ollama, ensure Ollama is running on localhost:11434
