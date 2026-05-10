---
name: deerflow-skill
description: DeerFlow agent orchestration for complex tasks requiring multi-step reasoning, web search, tool orchestration, or parallel subagent delegation. Use when user needs to research topics, search web, or delegate complex tasks to subagents. Triggers: 用deer, deer帮我, 调用deer, research, 搜索, 调研任务. 使用此 Skill 进行复杂任务的编排和执行。
---

# DeerFlow Agent

Invoke the DeerFlow agent system directly within Claude Code. No server required - runs embedded in the current process.

## Activation

```bash
python scripts/skill.py "your prompt here"
python scripts/skill.py --flash "quick task"
python scripts/skill.py --pro "complex task needing planning"
python scripts/skill.py --ultra "task requiring parallel subagent delegation"
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

- `DEEPSEEK_API_KEY` - DeepSeek API key (recommended, cost-effective)
- `TAVILY_API_KEY` - Tavily API key for web search
- `JINA_API_KEY` - Jina AI API key for web fetch

Alternative models: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`

## Examples

```bash
python scripts/skill.py "Research the latest developments in quantum computing"
python scripts/skill.py --flash "What is the capital of France?"
python scripts/skill.py --pro "Create a detailed project plan for building a REST API"
python scripts/skill.py --ultra "Analyze performance across all modules and identify bottlenecks"
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
