# Phase 1: Core Integration - Research

**Researched:** 2026-04-27
**Domain:** Claude Code skill with embedded Python agent orchestration
**Confidence:** HIGH

## Summary

Phase 1 establishes the minimal working skill that imports deerflow-harness, loads configuration, and invokes the agent. The architecture is a thin Python wrapper around `DeerFlowClient` - no HTTP, no server, pure embedded Python. The skill's primary responsibilities are: configuration path resolution, validation with actionable error messages, mode preset mapping, and basic agent invocation.

The core integration pattern is direct import: `from deerflow.client import DeerFlowClient`. All orchestration (config loading, model creation, tool assembly, middleware chain, agent execution) is delegated to DeerFlowClient. The skill validates initialization conditions upfront and provides clear error messages for common failure modes (missing config, missing package, missing credentials).

**Primary recommendation:** Use `DeerFlowClient.chat()` for simple one-shot responses; defer streaming to Phase 2.

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

**Skill Invocation:**
- Command format: `/deer-flow "your prompt here"` - prompt taken as argument
- Thread ID: Auto-generate UUID for each call (stateless by design)
- Model override: No model override flag - use config.yaml default (first model entry)
- Mode presets: Named presets with flags:
  - `--flash`: thinking=false, plan_mode=false, subagent=false (fastest)
  - `--standard`: thinking=true, plan_mode=false, subagent=false (default)
  - `--pro`: thinking=true, plan_mode=true, subagent=false
  - `--ultra`: thinking=true, plan_mode=true, subagent=true
- Default mode: Standard (balanced speed and quality)
- Output: Print response to stdout, let Claude Code handle display

**Config Resolution:**
- config.yaml path: Check in order:
  1. `DEER_FLOW_CONFIG_PATH` environment variable
  2. `./config.yaml` (current directory)
  3. `../config.yaml` (parent directory)
- Missing config.yaml: Auto-create `config.example.yaml` template with example model configs
- extensions_config.json: Look alongside config.yaml (same directory)
- Missing credentials: Show full guidance with missing env var names, example values, where to set them

**Skill Structure:**
- Core files: `SKILL.md`, `skill.py`, `scripts/`, `lib/`, `tests/`, `README.md`, `pyproject.toml`
- Python modules in lib/:
  - `config.py` - config path resolution, validation
  - `errors.py` - error message templates and formatting
  - `modes.py` - mode preset definitions and DeerFlowClient config mapping
- Entry point: `if __name__ == '__main__'` pattern in skill.py
- Dependency declaration: `pyproject.toml` with deerflow-harness as main dependency
- Scripts: `scripts/chat.sh` wrapper for quick shell usage
- Tests: `tests/` directory with unit tests for config resolution, error formatting, mode mapping

**Error Messages:**
- deerflow-harness not importable: Show pip/uv install commands
- config.yaml parse error: Show example content AND create config.example.yaml template
- Missing credentials: Full guidance format with env var names, example config.yaml, shell export commands
- LLM provider errors: Pass through raw error message (no wrapping)

### Claude's Discretion

- Exact error message wording and formatting
- config.example.yaml template content details
- Test coverage granularity
- README.md structure and example content

### Deferred Ideas (OUT OF SCOPE)

- Streaming support (Phase 2)
- MCP tool logging and status (Phase 3)
- Subagent delegation (Phase 4)
- Thread persistence/memory (v2+)

</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CORE-01 | Skill imports deerflow-harness package successfully | DeerFlowClient API documented; import pattern: `from deerflow.client import DeerFlowClient` |
| CORE-02 | Skill validates config.yaml exists and is parseable at initialization | `AppConfig.from_file()` handles YAML parsing; wrap in try/except for clear errors |
| CORE-03 | Skill validates required credentials are present in config | Check model configs have non-empty api_key after env var expansion |
| CORE-04 | Skill creates DeerFlowClient instance with loaded configuration | `DeerFlowClient(config_path=resolved_path)` constructor |
| CORE-05 | Skill invokes agent and receives response for single user message | `client.chat(message)` returns string response |
| CONF-01 | Skill resolves config.yaml path via DEER_FLOW_CONFIG_PATH or default locations | Custom resolution needed: check DEER_FLOW_CONFIG_PATH -> ./config.yaml -> ../config.yaml |
| CONF-02 | Skill supports environment variable expansion in config values | `AppConfig.resolve_env_variables()` handles `$VAR` syntax automatically |
| CONF-03 | Skill provides actionable error message when config.yaml missing | Create config.example.yaml template; show install guidance |
| CONF-04 | Skill provides actionable error message when deerflow-harness not importable | Wrap import in try/except; show pip/uv install commands |
| LLM-01 | Skill supports OpenAI models via config.yaml model.use | `langchain_openai:ChatOpenAI` in model.use field |
| LLM-02 | Skill supports Anthropic models via config.yaml model.use | `langchain_anthropic:ChatAnthropic` in model.use field |
| LLM-03 | Skill supports local models (Ollama) via config.yaml model.use | `langchain_ollama:ChatOllama` in model.use field (optional dependency) |
| LLM-04 | Skill reports clear error when model credentials missing | Validate api_key field after env var expansion; show guidance |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| deerflow-harness | 0.1.0 | Agent framework | Core package providing DeerFlowClient, tool registry, MCP integration |
| Python | 3.12+ | Runtime | deerflow-harness requires modern Python features |
| LangGraph | 1.0.6-1.0.9 | Agent runtime | Structured agent workflows with middleware chain |
| Pydantic | 2.12.5+ | Configuration | deer-flow's config system is Pydantic-based with env var expansion |
| PyYAML | 6.0.3+ | Config parsing | YAML config file support |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| langchain-openai | 1.1.7+ | OpenAI LLM | When using GPT models |
| langchain-anthropic | 1.3.4+ | Anthropic LLM | When using Claude models |
| langchain-ollama | 0.3.0+ | Ollama LLM | When using local models (optional) |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| deerflow-harness | Custom agent implementation | deerflow-harness provides mature orchestration, MCP integration, middleware chain - custom would require weeks of work |
| DeerFlowClient.chat() | DeerFlowClient.stream() | chat() is simpler for Phase 1; stream() adds complexity deferred to Phase 2 |

**Installation:**
```bash
# As dependency in pyproject.toml
dependencies = ["deerflow-harness>=0.1.0"]

# Or with uv
uv add deerflow-harness

# Optional: local workspace dependency
# dependencies = ["deerflow-harness @ file:///path/to/deer-flow/backend/packages/harness"]
```

## Architecture Patterns

### Recommended Project Structure
```
src/
├── SKILL.md              # Claude Code skill definition with YAML frontmatter
├── skill.py              # Thin entry point importing DeerFlowClient
├── lib/
│   ├── __init__.py       # Package marker
│   ├── config.py         # Config path resolution, validation
│   ├── errors.py         # Error message templates and formatting
│   └── modes.py          # Mode preset definitions and DeerFlowClient mapping
├── scripts/
│   └── chat.sh           # Shell wrapper for quick usage
├── tests/
│   ├── __init__.py
│   ├── test_config.py    # Config resolution, validation tests
│   ├── test_errors.py    # Error message formatting tests
│   └── test_modes.py     # Mode preset mapping tests
├── README.md             # Usage documentation
└── pyproject.toml        # Dependencies and build config
```

### Pattern 1: Thin Wrapper Entry Point
**What:** skill.py imports DeerFlowClient directly, handles CLI args, calls client.chat()
**When to use:** Always - this is the core pattern for embedded skills
**Example:**
```python
# skill.py
import sys
import uuid
from deerflow.client import DeerFlowClient
from lib.config import resolve_config_path, validate_config
from lib.errors import format_error
from lib.modes import get_mode_config

def main():
    try:
        # Parse args
        args = parse_args(sys.argv[1:])
        
        # Resolve and validate config
        config_path = resolve_config_path()
        validate_config(config_path)
        
        # Create client with mode settings
        mode_config = get_mode_config(args.mode)
        client = DeerFlowClient(config_path=str(config_path), **mode_config)
        
        # Invoke agent
        response = client.chat(args.prompt)
        print(response)
        
    except Exception as e:
        print(format_error(e), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```
**Source:** deerflow/client.py + SKILL.md pattern from skills/public/deep-research/

### Pattern 2: Config Path Resolution
**What:** Custom resolution order matching user requirements
**When to use:** At skill initialization before creating DeerFlowClient
**Example:**
```python
# lib/config.py
import os
from pathlib import Path

def resolve_config_path() -> Path:
    """Resolve config.yaml path in priority order."""
    # 1. Environment variable
    if env_path := os.getenv("DEER_FLOW_CONFIG_PATH"):
        path = Path(env_path)
        if path.exists():
            return path
        raise FileNotFoundError(f"Config not found at DEER_FLOW_CONFIG_PATH: {path}")
    
    # 2. Current directory
    cwd_config = Path.cwd() / "config.yaml"
    if cwd_config.exists():
        return cwd_config
    
    # 3. Parent directory
    parent_config = Path.cwd().parent / "config.yaml"
    if parent_config.exists():
        return parent_config
    
    # Not found - create example template
    create_example_config()
    raise FileNotFoundError("config.yaml not found. Created config.example.yaml with template.")
```
**Source:** CONTEXT.md decisions + deerflow/config/app_config.py pattern

### Pattern 3: Mode Preset Mapping
**What:** Map CLI flags to DeerFlowClient constructor arguments
**When to use:** When constructing DeerFlowClient instance
**Example:**
```python
# lib/modes.py
from dataclasses import dataclass

@dataclass
class ModeConfig:
    thinking_enabled: bool
    plan_mode: bool
    subagent_enabled: bool

MODE_PRESETS = {
    "flash": ModeConfig(thinking_enabled=False, plan_mode=False, subagent_enabled=False),
    "standard": ModeConfig(thinking_enabled=True, plan_mode=False, subagent_enabled=False),
    "pro": ModeConfig(thinking_enabled=True, plan_mode=True, subagent_enabled=False),
    "ultra": ModeConfig(thinking_enabled=True, plan_mode=True, subagent_enabled=True),
}

def get_mode_config(mode: str = "standard") -> dict:
    """Get DeerFlowClient kwargs for mode preset."""
    if mode not in MODE_PRESETS:
        raise ValueError(f"Unknown mode: {mode}. Available: {list(MODE_PRESETS.keys())}")
    config = MODE_PRESETS[mode]
    return {
        "thinking_enabled": config.thinking_enabled,
        "plan_mode": config.plan_mode,
        "subagent_enabled": config.subagent_enabled,
    }
```
**Source:** CONTEXT.md mode preset decisions

### Anti-Patterns to Avoid
- **Wrapping LLM errors:** Pass through raw provider errors, don't add extra wrapping
- **Lazy config validation:** Validate config exists and has credentials BEFORE creating client, not on first LLM call
- **Stateful design:** Each invocation should be independent; no thread persistence in Phase 1

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Agent orchestration | Custom agent loop | DeerFlowClient | Mature middleware chain, MCP integration, error handling |
| Config loading | Custom YAML parsing | AppConfig.from_file() | Env var expansion, validation, all config sections |
| Tool assembly | Manual tool registration | get_available_tools() | Handles builtins, MCP, deduplication |
| Model creation | Manual LLM instantiation | create_chat_model() | Multi-provider support, thinking mode config |
| Error formatting | Custom error types | deerflow errors module | Consistent messaging, install guidance |

**Key insight:** deerflow-harness provides complete implementation - skill is purely configuration + error messaging

## Common Pitfalls

### Pitfall 1: Missing deerflow-harness Package
**What goes wrong:** ImportError when skill.py runs
**Why it happens:** Package not installed or not in Python path
**How to avoid:** Wrap import in try/except with clear install instructions
**Warning signs:** ImportError: No module named 'deerflow'
**Example handling:**
```python
try:
    from deerflow.client import DeerFlowClient
except ImportError:
    print("""deerflow-harness is not installed. Install with:
    pip install deerflow-harness
or:
    uv add deerflow-harness
""", file=sys.stderr)
    sys.exit(1)
```

### Pitfall 2: Missing or Invalid config.yaml
**What goes wrong:** FileNotFoundError or yaml.YAMLError at startup
**Why it happens:** User hasn't created config, or config has syntax errors
**How to avoid:** 
1. Custom resolution with clear error message
2. Auto-create config.example.yaml template when missing
3. Wrap AppConfig.from_file() with actionable error guidance
**Warning signs:** FileNotFoundError, yaml.scanner.ScannerError
**Example template:**
```yaml
# config.example.yaml
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

### Pitfall 3: Missing Credentials in Config
**What goes wrong:** LLM API errors on first request (401 Unauthorized)
**Why it happens:** api_key field is empty after env var expansion
**How to avoid:** Validate model configs have non-empty api_key at initialization
**Warning signs:** api_key: "" or api_key: "$MISSING_VAR"
**Example validation:**
```python
def validate_credentials(config_path: Path) -> None:
    """Check that required credentials are present."""
    from deerflow.config.app_config import AppConfig
    config = AppConfig.from_file(str(config_path))
    
    missing = []
    for model in config.models:
        if not model.api_key or model.api_key.startswith("$"):
            missing.append(f"{model.name}: api_key not set")
    
    if missing:
        print(f"""Missing required credentials:
  {chr(10).join('  - ' + m for m in missing)}

Example config.yaml:
  models:
    - name: gpt-4
      use: langchain_openai:ChatOpenAI
      api_key: "$OPENAI_API_KEY"

Or set in shell:
  export OPENAI_API_KEY=sk-...
""", file=sys.stderr)
        sys.exit(1)
```

### Pitfall 4: Config Path Resolution Differs from deer-flow Default
**What goes wrong:** Skill finds different config.yaml than user expects
**Why it happens:** deer-flow has built-in resolution (backend/config.yaml, repo-root/config.yaml); skill needs custom order (./config.yaml, ../config.yaml)
**How to avoid:** Implement custom resolution in lib/config.py, don't rely on deer-flow's default resolution
**Warning signs:** Config loaded from unexpected location

## Code Examples

### Basic Skill Invocation (skill.py)
```python
#!/usr/bin/env python3
"""DeerFlow Claude Code skill entry point."""
import sys
import uuid
from pathlib import Path

# Add lib to path for local imports
sys.path.insert(0, str(Path(__file__).parent))

try:
    from deerflow.client import DeerFlowClient
except ImportError as e:
    print(f"""deerflow-harness is not installed. Install with:
    pip install deerflow-harness
or:
    uv add deerflow-harness
""", file=sys.stderr)
    sys.exit(1)

from lib.config import resolve_and_validate_config
from lib.modes import get_mode_config
from lib.errors import format_error

def parse_args(argv: list[str]) -> tuple[str, str]:
    """Parse CLI arguments: [--flash|--standard|--pro|--ultra] prompt"""
    mode = "standard"
    args = argv[:]
    
    if args and args[0].startswith("--"):
        mode = args.pop(0)[2:]
    
    if not args:
        raise ValueError("Usage: deer-flow [--flash|--standard|--pro|--ultra] \"prompt\"")
    
    return mode, " ".join(args)

def main():
    try:
        mode, prompt = parse_args(sys.argv[1:])
        config_path = resolve_and_validate_config()
        client_kwargs = get_mode_config(mode)
        
        client = DeerFlowClient(config_path=str(config_path), **client_kwargs)
        response = client.chat(prompt)
        print(response)
        
    except Exception as e:
        print(format_error(e), file=sys.stderr)
        sys.exit(1)

if __name__ == '__main__':
    main()
```
**Source:** deerflow/client.py API + CONTEXT.md decisions

### SKILL.md Format
```yaml
---
name: deer-flow
description: Invoke deer-flow agent orchestration directly in Claude Code. Use for complex tasks requiring multi-step reasoning, tool orchestration, or subagent delegation. Supports mode presets: --flash (fastest), --standard (default), --pro (with planning), --ultra (with subagents).
---

# DeerFlow Skill

## Overview

Invoke the deer-flow agent system directly within Claude Code. No server required - runs embedded in the current process.

## Usage

```
/deer-flow "your prompt here"
/deer-flow --flash "quick task"
/deer-flow --pro "complex task requiring planning"
/deer-flow --ultra "task requiring parallel subagent delegation"
```

## Configuration

Requires `config.yaml` with model credentials. Skill will auto-create `config.example.yaml` template if missing.
```
**Source:** skills/public/deep-research/SKILL.md pattern

### pyproject.toml
```toml
[project]
name = "deerflow-skill"
version = "0.1.0"
description = "Claude Code skill for deer-flow agent orchestration"
requires-python = ">=3.12"
dependencies = [
    "deerflow-harness>=0.1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-cov>=4.0.0",
]

[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Server-based agent | Embedded agent (DeerFlowClient) | deerflow-harness 0.1.0 | No HTTP overhead, direct Python import |
| Custom config resolution | AppConfig.from_file() | deerflow-harness 0.1.0 | Standardized config with env var expansion |
| Manual tool assembly | get_available_tools() | deerflow-harness 0.1.0 | Automatic MCP integration, deduplication |

**Deprecated/outdated:**
- Gateway API for skills: Use DeerFlowClient directly instead - simpler, no HTTP overhead

## Open Questions

1. **deerflow-harness PyPI availability**
   - What we know: Package defined at ~/project/deer-flow/backend/packages/harness/
   - What's unclear: Is it published to PyPI or needs local workspace dependency?
   - Recommendation: Add both options to pyproject.toml; document local install path in README

2. **Claude Code skill invocation mechanism**
   - What we know: SKILL.md format with YAML frontmatter
   - What's unclear: Exact pattern for Claude Code invoking Python skills
   - Recommendation: Test SKILL.md format early in Wave 0

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ |
| Config file | pyproject.toml [tool.pytest.ini_options] |
| Quick run command | `pytest tests/ -x -q` |
| Full suite command | `pytest tests/ -v --cov=lib` |

### Phase Requirements -> Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CORE-01 | Imports deerflow-harness | unit | `pytest tests/test_imports.py -x` | Wave 0 |
| CORE-02 | Validates config.yaml exists | unit | `pytest tests/test_config.py::test_config_exists -x` | Wave 0 |
| CORE-03 | Validates credentials present | unit | `pytest tests/test_config.py::test_credentials_present -x` | Wave 0 |
| CORE-04 | Creates DeerFlowClient | unit | `pytest tests/test_client.py::test_client_creation -x` | Wave 0 |
| CORE-05 | Invokes agent, gets response | integration | `pytest tests/test_client.py::test_chat -x` | Wave 0 |
| CONF-01 | Resolves config path order | unit | `pytest tests/test_config.py::test_path_resolution -x` | Wave 0 |
| CONF-02 | Expands env vars | unit | `pytest tests/test_config.py::test_env_expansion -x` | Wave 0 |
| CONF-03 | Error on missing config | unit | `pytest tests/test_errors.py::test_missing_config_error -x` | Wave 0 |
| CONF-04 | Error on missing package | unit | `pytest tests/test_errors.py::test_missing_package_error -x` | Wave 0 |
| LLM-01 | Supports OpenAI models | integration | `pytest tests/test_models.py::test_openai_model -x` | Wave 0 |
| LLM-02 | Supports Anthropic models | integration | `pytest tests/test_models.py::test_anthropic_model -x` | Wave 0 |
| LLM-03 | Supports Ollama models | integration | `pytest tests/test_models.py::test_ollama_model -x` | Wave 0 |
| LLM-04 | Error on missing credentials | unit | `pytest tests/test_errors.py::test_missing_credentials_error -x` | Wave 0 |

### Sampling Rate
- **Per task commit:** `pytest tests/ -x -q`
- **Per wave merge:** `pytest tests/ -v --cov=lib`
- **Phase gate:** Full suite green before `/gsd:verify-work`

### Wave 0 Gaps
- [ ] `tests/test_imports.py` - verifies deerflow-harness importable
- [ ] `tests/test_config.py` - config resolution and validation
- [ ] `tests/test_errors.py` - error message formatting
- [ ] `tests/test_modes.py` - mode preset mapping
- [ ] `tests/test_client.py` - DeerFlowClient creation and chat
- [ ] `tests/test_models.py` - multi-provider model support
- [ ] `tests/conftest.py` - shared fixtures (mock config, mock client)

## Sources

### Primary (HIGH confidence)
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/client.py` - DeerFlowClient API, stream/chat methods
- `/Users/wuliang/project/deer-flow/backend/packages/harness/deerflow/config/app_config.py` - Config loading with env var expansion
- `/Users/wuliang/project/deer-flow/backend/packages/harness/pyproject.toml` - deerflow-harness dependencies
- `/Users/wuliang/project/deer-flow/skills/public/deep-research/SKILL.md` - Skill format reference

### Secondary (MEDIUM confidence)
- `.planning/phases/01-core-integration/01-CONTEXT.md` - User decisions for implementation
- `.planning/research/SUMMARY.md` - Domain research summary

### Tertiary (LOW confidence)
- None - all critical information from primary sources

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Direct codebase analysis of deerflow-harness
- Architecture: HIGH - DeerFlowClient API is well-documented in source
- Pitfalls: MEDIUM - Derived from code analysis; some runtime behaviors may need validation

**Research date:** 2026-04-27
**Valid until:** 30 days (stable Python/LangGraph ecosystem)
