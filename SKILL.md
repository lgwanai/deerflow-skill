---
name: deer
description: DeerFlow agent orchestration for complex tasks requiring multi-step reasoning, web search, or parallel subagent delegation. Triggers: 用deer, deer帮我, 调用deer, research task, complex query.
---

# DeerFlow Agent

Invoke the DeerFlow agent system directly. No server required.

## Usage

```bash
python scripts/skill.py "your prompt"
python scripts/skill.py --flash "quick task"
python scripts/skill.py --pro "complex task"
python scripts/skill.py --ultra "parallel delegation"
```

## Modes

| Mode | Thinking | Planning | Subagents |
|------|----------|----------|-----------|
| --flash | No | No | No |
| --standard | Yes | No | No |
| --pro | Yes | Yes | No |
| --ultra | Yes | Yes | Yes |

## Setup

Copy `config.example.yaml` to `config.yaml` and add API keys:

- DEEPSEEK_API_KEY
- TAVILY_API_KEY  
- JINA_API_KEY

## Dependencies

```bash
pip install langchain langchain-anthropic langchain-openai tavily-python httpx
```
