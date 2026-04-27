# Pitfalls Research

**Domain:** Claude Code skill with embedded agent orchestration (deerflow-harness)
**Researched:** 2026-04-27
**Confidence:** MEDIUM (based on deer-flow source analysis and MCP documentation)

## Critical Pitfalls

### Pitfall 1: Missing or Invalid config.yaml

**What goes wrong:**
Skill fails silently or crashes when deer-flow's `config.yaml` is missing, malformed, or lacks required model credentials. The skill appears to initialize but throws `FileNotFoundError` or validation errors when the agent tries to make LLM calls.

**Why it happens:**
DeerFlow's `AppConfig.from_file()` has a three-step resolution:
1. Check `config_path` parameter
2. Check `DEER_FLOW_CONFIG_PATH` environment variable
3. Search deterministic backend/repository-root defaults

If none are found, it raises `FileNotFoundError`. Even if found, YAML parsing or Pydantic validation may fail on malformed config.

**How to avoid:**
1. Provide a clear error message at skill initialization if `config.yaml` cannot be located
2. Validate model credentials during initialization (not lazily on first call)
3. Document the expected `config.yaml` location and schema
4. Consider bundling a minimal `config.example.yaml` template

**Warning signs:**
- Skill initializes but first agent call fails with `FileNotFoundError: config.yaml`
- Agent hangs on first LLM call (model credentials not loaded)
- Pydantic validation errors in stderr logs

**Phase to address:**
Phase 1 (Core Integration) — initialization and configuration validation

---

### Pitfall 2: deerflow-harness Package Not Importable

**What goes wrong:**
Skill imports `deerflow-harness` but fails at runtime with `ModuleNotFoundError` or `ImportError`. This occurs when the package is not installed in the Python environment where Claude Code runs the skill.

**Why it happens:**
Claude Code skills run Python code, but the skill doesn't manage Python dependencies. Users may have deer-flow installed in a different environment, or the package may not be published/accessible.

**How to avoid:**
1. Use try/except around the import and provide actionable error message
2. Document installation requirements (`pip install deerflow-harness` or `uv add deerflow-harness`)
3. Consider checking for package availability before attempting to use it
4. Provide fallback behavior or graceful degradation message

**Warning signs:**
- Immediate `ModuleNotFoundError: No module named 'deerflow'`
- Import-time side effects (background threads) start before config loading

**Phase to address:**
Phase 1 (Core Integration) — dependency validation and error handling

---

### Pitfall 3: Recursion Limit Exceeded (Agent Loop)

**What goes wrong:**
Agent enters an infinite or long-running tool-calling loop, eventually hitting LangGraph's recursion limit (default 100). The skill appears to hang, then fails with a recursion limit error.

**Why it happens:**
- Tool returns results that trigger the same tool again (circular dependency)
- Model keeps calling tools without progressing toward completion
- Subagent delegation creates nested loops without proper termination conditions
- No `max_turns` or `recursion_limit` configured for the use case

**How to avoid:**
1. Configure reasonable defaults: `recursion_limit=100` for main agent, `max_turns=50` for subagents
2. Expose recursion limit as configurable in skill parameters
3. Log when approaching recursion limits (e.g., at 80%)
4. Implement early termination for repetitive tool calls

**Warning signs:**
- Agent runs for extended time without producing output
- Same tool called multiple times with similar parameters
- Logs show repeated message/tool_call cycles

**Phase to address:**
Phase 2 (Tool Calling) — recursion limit configuration and monitoring

---

### Pitfall 4: MCP Tool Initialization Fails Silently

**What goes wrong:**
MCP servers configured in `extensions_config.json` fail to connect, but the skill proceeds with a reduced tool set. Users don't realize why expected tools are missing.

**Why it happens:**
DeerFlow's MCP initialization catches exceptions and logs them but doesn't fail the agent startup. The `get_cached_mcp_tools()` function silently returns an empty list on failure.

**How to avoid:**
1. Log MCP initialization status clearly (connected vs. failed vs. disabled)
2. Expose MCP server status through a query API in the skill
3. Warn users when expected tools are not available
4. Provide guidance on MCP server troubleshooting (use MCP Inspector)

**Warning signs:**
- Fewer tools available than expected
- `Warning: Failed to initialize MCP tools:` in logs
- Tools that were working before suddenly disappear

**Phase to address:**
Phase 3 (MCP Integration) — MCP error visibility and status reporting

---

### Pitfall 5: Thread State Loss (No Checkpointer)

**What goes wrong:**
Multi-turn conversations don't maintain context between calls. Each invocation starts fresh, losing all previous conversation history.

**Why it happens:**
DeerFlowClient's doc explicitly states: "Multi-turn conversations require a checkpointer. Without one, each stream() / chat() call is stateless — thread_id is only used for file isolation."

**How to avoid:**
1. Configure a checkpointer in `config.yaml` (sqlite or postgres)
2. Document that stateless mode is intentional (no thread persistence)
3. If stateless is intentional, make that clear in skill interface
4. Provide thread_id generation/use guidance

**Warning signs:**
- Agent doesn't remember previous messages
- Context window underutilized (no history accumulated)
- File uploads work but conversation doesn't continue

**Phase to address:**
Phase 1 (Core Integration) — checkpointer configuration documentation

---

### Pitfall 6: Subagent Timeout Without Clear Feedback

**What goes wrong:**
Subagent delegation times out (default 900s/15min) but the error message doesn't clearly indicate what happened or how to fix it.

**Why it happens:**
DeerFlow's `SubagentExecutor` catches `FuturesTimeoutError` and sets status to `TIMED_OUT`, but the error message may not propagate clearly to the skill user.

**How to avoid:**
1. Wrap subagent calls with explicit timeout handling
2. Provide clear timeout messages: "Subagent X timed out after Y seconds"
3. Document default timeouts and how to configure them
4. Allow timeout configuration through skill parameters

**Warning signs:**
- Long-running tasks fail after exactly 900 seconds
- Error message mentions "timed out" but not which subagent
- Partial progress lost when timeout occurs

**Phase to address:**
Phase 4 (Subagent Delegation) — timeout configuration and error reporting

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| Skip config validation at init | Faster startup | Cryptic errors later | Never |
| Use default recursion limit | Less code | Infinite loops | MVP only, document clearly |
| Ignore MCP initialization errors | Graceful degradation | Missing tools, user confusion | Never — always log warnings |
| Hard-code model name | Simpler config | Can't switch models, breaks if model deprecated | Never — use config.yaml |
| No timeout on agent calls | Task completes eventually | Hangs, resource exhaustion | Never |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| deerflow-harness | Import without try/except | Wrap import, provide actionable error message |
| config.yaml | Assume it's in cwd | Use `DEER_FLOW_CONFIG_PATH` env var or explicit path |
| MCP servers | Expect MCP to work without config | Require extensions_config.json, validate MCP server connectivity |
| Model providers | Hard-code API keys | Use environment variables ($OPENAI_API_KEY) in config.yaml |
| Checkpointer | Omit for multi-turn | Configure sqlite checkpointer for persistence |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| No recursion limit | Agent hangs, high CPU | Set recursion_limit=100 | Complex tasks |
| MCP tools loaded synchronously | Slow startup, blocking | DeerFlow uses lazy init via get_cached_mcp_tools() | Many MCP servers |
| Large tool output not truncated | Memory bloat | Use DeerFlow's output_max_chars config | Large file reads |
| No subagent count limit | Resource exhaustion | DeerFlow has max_concurrent_subagents=3 | Parallel task delegation |
| Thread leak in subagent executor | Memory leak over time | Use global thread pools with cleanup | Long-running skill process |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| Accepting unvalidated thread_id | Path traversal in uploads | Validate thread_id format (UUID) before use |
| No sandbox isolation | Code execution in user context | Document that skill runs in Claude Code environment (no sandbox) |
| MCP server commands from untrusted source | Arbitrary code execution | Only use MCP servers from extensions_config.json controlled by user |
| Logging API keys | Credential exposure | DeerFlow resolves $VAR at config load time, ensure logs don't echo raw config |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| Silent failure on missing config | Confusion, "it doesn't work" | Immediate, actionable error: "config.yaml not found at $PATH. See docs: $URL" |
| No progress indication for long tasks | User thinks it's stuck | Stream events with progress, show tool calls in progress |
| Cryptic recursion limit errors | User doesn't know what happened | Clear message: "Agent reached step limit. Try simplifying your request." |
| Missing tools without warning | Unexpected behavior | Log at startup: "MCP server X failed: $ERROR. Tools available: Y" |
| No way to check agent status | No visibility into running skill | Expose status query API (models, skills, MCP servers) |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [ ] **Config Loading:** Skill loads config file — verify it also validates required fields (models, credentials)
- [ ] **Agent Initialization:** Agent object created — verify it can make successful LLM calls
- [ ] **Tool Discovery:** Tools list returned — verify MCP tools actually connect and work
- [ ] **Streaming:** Events emitted — verify errors are also streamed, not silently swallowed
- [ ] **Error Messages:** Errors printed — verify they include actionable guidance, not just stack traces
- [ ] **Documented Requirements:** README mentions dependencies — verify exact versions and install commands work

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| Missing config.yaml | LOW | Create config.yaml from config.example.yaml template |
| Import error | LOW | Install deerflow-harness, restart skill |
| Recursion limit | MEDIUM | Simplify task, increase limit, or debug tool loop |
| MCP connection failure | MEDIUM | Use MCP Inspector to debug, check server config |
| No checkpointer | HIGH | For stateless use: document as intentional. For state: add sqlite checkpointer config |
| Subagent timeout | MEDIUM | Increase timeout_seconds in config, or split task |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| Missing/Invalid config.yaml | Phase 1 (Core Integration) | Unit test: skill fails gracefully without config |
| deerflow-harness not importable | Phase 1 (Core Integration) | Unit test: import wrapped with clear error message |
| Recursion limit exceeded | Phase 2 (Tool Calling) | Integration test: complex task completes within limits |
| MCP tool initialization fails | Phase 3 (MCP Integration) | Unit test: MCP init failure logs warning, skill continues |
| Thread state loss | Phase 1 (Core Integration) | Doc: stateless mode documented, checkpointer config explained |
| Subagent timeout | Phase 4 (Subagent Delegation) | Integration test: timeout produces clear error message |

## Sources

- [MCP Debugging Guide](https://modelcontextprotocol.io/docs/tools/debugging) — Common MCP issues and logging strategies
- [MCP Tools Specification](https://modelcontextprotocol.io/specification/latest/server/tools) — Tool calling protocol and error handling
- deer-flow source code analysis (client.py, app_config.py, mcp/cache.py, subagents/executor.py) — Configuration loading, MCP initialization, subagent execution patterns
- config.example.yaml — Configuration schema and patterns

---
*Pitfalls research for: Claude Code skill with embedded agent orchestration*
*Researched: 2026-04-27*
