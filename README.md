# DeerFlow Skill

Embed DeerFlow agent orchestration into Claude Code. No server required - runs embedded in the current process.

基于 [deer-flow](https://github.com/bytedance/deer-flow) 内核，持续同步上游更新。

## Quick Start

```bash
# 1. Copy config template
cp config.example.yaml config.yaml

# 2. Edit config.yaml and add your API keys

# 3. Run the skill
./scripts/chat.sh --flash "your question"
```

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
- **Subagent Delegation**: Parallel task execution with specialized agents (persistent event loop)
- **Async/Sync Bridge**: Automatic sync wrapper for async-only tools via `tools/sync.py`
- **Loop Detection**: Configurable loop detection with per-tool frequency threshold overrides
- **Token Tracking**: Subagent token usage collection and reporting
- **Agent Updates**: Runtime agent configuration updates via `update_agent_tool`

## Configuration

Edit `config.yaml` with your credentials:

```yaml
models:
  - name: deepseek-v4-flash
    use: langchain_anthropic:ChatAnthropic
    model: deepseek-v4-flash
    api_key: $DEEPSEEK_API_KEY
    base_url: https://api.deepseek.com/anthropic

tools:
  - name: web_search
    use: deerflow.community.tavily.tools:web_search_tool
    api_key: $TAVILY_API_KEY

  - name: web_fetch
    use: deerflow.community.jina_ai.tools:web_fetch_tool
    api_key: $JINA_API_KEY
```

### Required API Keys

| Key | Service | Get it from |
|-----|---------|-------------|
| `DEEPSEEK_API_KEY` | DeepSeek models | https://platform.deepseek.com |
| `TAVILY_API_KEY` | Web search | https://tavily.com |
| `JINA_API_KEY` | Web fetch | https://jina.ai/reader |

## Project Structure

```
deerflow-skill/
├── SKILL.md              # Skill definition
├── config.yaml           # Your configuration (gitignored)
├── config.example.yaml   # Configuration template
├── scripts/
│   ├── skill.py          # Main entry point
│   ├── chat.sh           # Shell wrapper
│   └── package.sh        # Packaging script
├── deerflow/             # Embedded deer-flow core
│   ├── client.py         # DeerFlowClient API
│   ├── agents/           # Agent orchestration + middlewares
│   ├── tools/            # Tools + sync wrapper + types
│   ├── config/           # 20+ configuration models
│   ├── community/        # Tavily, Jina, Firecrawl, etc.
│   ├── subagents/        # Subagent executor + token collector
│   ├── runtime/          # Checkpointer, runs, user_context
│   ├── skills/           # Skill manager + storage + tool_policy
│   ├── models/           # LLM providers (Claude, DeepSeek, OpenAI)
│   ├── sandbox/          # Local sandbox execution
│   ├── mcp/              # MCP protocol client
│   └── utils/            # Network, readability, time
├── lib/                  # Skill helper utilities
├── tests/                # Test suite
└── dist/                 # Packaged zip output
```

## Packaging

```bash
./scripts/package.sh
```

Output: `dist/deerflow-skill-YYYYMMDD.zip` (~390KB, excludes .gitignore files)

## Examples

```bash
# Quick question
./scripts/chat.sh --flash "What is quantum computing?"

# Research task
./scripts/chat.sh "Research the latest AI developments"

# Complex task with planning
./scripts/chat.sh --pro "Create a project plan for building a REST API"

# Parallel analysis
./scripts/chat.sh --ultra "Analyze performance across all modules"

# Research and save to file (stderr logs stay in terminal)
./scripts/chat.sh --flash "Research Tesla vs BYD" > report.md
```

## Development

### Run Tests

```bash
python -m pytest tests/
```

### Dependencies

```bash
pip install langchain langchain-anthropic langchain-openai tavily-python httpx pyyaml
```

## License

MIT
