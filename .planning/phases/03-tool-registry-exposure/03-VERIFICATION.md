---
phase: 03-tool-registry-exposure
verified: 2026-04-27T14:30:00Z
status: gaps_found
score: 2/5 must-haves verified
gaps:
  - truth: "User sees built-in tools (bash, read, write, str_replace) are available"
    status: partial
    reason: "log_available_tools function exists and tested, but NOT wired into skill.py entry point"
    artifacts:
      - path: "skill.py"
        issue: "Does not import or call lib.tools.log_available_tools"
    missing:
      - "Import lib.tools in skill.py"
      - "Call log_available_tools() after DeerFlowClient creation"
  - truth: "User sees MCP tools loaded from extensions_config.json"
    status: partial
    reason: "get_mcp_tool_names and log_mcp_status functions exist, but NOT wired into skill.py"
    artifacts:
      - path: "skill.py"
        issue: "Does not import or call lib.tools MCP functions"
    missing:
      - "Import lib.tools in skill.py"
      - "Call log_mcp_status() with enabled MCP servers"
  - truth: "User is warned when expected MCP tools are unavailable"
    status: partial
    reason: "check_mcp_tool_availability function exists and tested, but NOT wired into skill.py"
    artifacts:
      - path: "skill.py"
        issue: "Does not import or call lib.tools.check_mcp_tool_availability"
    missing:
      - "Call check_mcp_tool_availability() after MCP tools loaded"
---

# Phase 03: Tool Registry Exposure Verification Report

**Phase Goal:** Full tool ecosystem available including MCP tools
**Verified:** 2026-04-27T14:30:00Z
**Status:** gaps_found
**Re-verification:** No - initial verification

## Goal Achievement

### Observable Truths

| #   | Truth | Status | Evidence |
| --- | ----- | ------ | -------- |
| 1 | User can use deer-flow's built-in tools (bash, read, write, str_replace) | ? NEEDS HUMAN | deerflow-harness loads tools; skill.py does not log them |
| 2 | User can use tools from configured MCP servers | ? NEEDS HUMAN | deerflow-harness loads MCP tools; skill.py does not log them |
| 3 | User sees clear log of which MCP tools loaded successfully | PARTIAL | log_mcp_status() exists, NOT wired |
| 4 | User is warned when expected MCP tools are unavailable | PARTIAL | check_mcp_tool_availability() exists, NOT wired |
| 5 | User sees tools are deduplicated by name | VERIFIED | get_unique_tool_names() tested, deerflow-harness handles internally |

**Score:** 0.5/4 core truths fully verified (deduplication is handled by deerflow-harness, not observable by user)

### Required Artifacts

| Artifact | Expected | Status | Details |
| -------- | -------- | ------ | ------- |
| `lib/tools.py` | Tool logging functions | VERIFIED | 127 lines, 5 functions exported |
| `tests/test_tool_registry.py` | TOOL-01 through TOOL-05 tests | VERIFIED | 189 lines, 6 passing tests |
| `tests/conftest.py` | Mock fixtures for tool registry | VERIFIED | 4 Phase 3 fixtures added |
| `skill.py` | Entry point calling tool logging | ORPHANED | Does NOT import lib.tools |

### Key Link Verification

| From | To | Via | Status | Details |
| ---- | -- | --- | ------ | ------- |
| `lib/tools.py` | `deerflow.tools.get_available_tools` | runtime import | NOT_WIRED | No direct import; functions receive tools as parameters |
| `skill.py` | `lib/tools.py` | import | NOT_WIRED | skill.py does not import lib.tools at all |
| `skill.py` | `lib.tools.log_available_tools` | function call | NOT_WIRED | Function exists but never called |
| `skill.py` | `lib.tools.log_mcp_status` | function call | NOT_WIRED | Function exists but never called |
| `skill.py` | `lib.tools.check_mcp_tool_availability` | function call | NOT_WIRED | Function exists but never called |

### Requirements Coverage

| Requirement | Source Plan | Description | Status | Evidence |
| ----------- | ---------- | ----------- | ------ | -------- |
| TOOL-01 | 03-01 | Skill exposes built-in tools (bash, read, write, str_replace) | BLOCKED | log_available_tools exists but NOT called |
| TOOL-02 | 03-02 | Skill loads MCP tools from extensions_config.json | SATISFIED | deerflow-harness handles this; get_mcp_tool_names available |
| TOOL-03 | 03-01 | Skill deduplicates tools by name across sources | SATISFIED | deerflow-harness handles internally; get_unique_tool_names helper exists |
| TOOL-04 | 03-02 | Skill logs MCP tool initialization status clearly | BLOCKED | log_mcp_status exists but NOT called |
| TOOL-05 | 03-02 | Skill warns when expected MCP tools are unavailable | BLOCKED | check_mcp_tool_availability exists but NOT called |

**Orphaned Requirements:** None - all TOOL-* IDs are accounted for in plans.

### Anti-Patterns Found

| File | Line | Pattern | Severity | Impact |
| ---- | ---- | ------- | -------- | ------ |
| lib/tools.py | - | No TODO/FIXME | N/A | Clean code |
| tests/test_tool_registry.py | - | No TODO/FIXME | N/A | Clean code |

**Note:** No blocker anti-patterns found. Code is clean and well-structured.

### Human Verification Required

#### 1. Tool Exposure Verification

**Test:** Run `python skill.py "test prompt"` with valid deerflow config
**Expected:** User should see tool names logged to stderr during initialization
**Why human:** Requires running skill with real deerflow-harness and observing stderr output
**Current issue:** No tool logging will appear because skill.py does not call the logging functions

#### 2. MCP Tool Logging

**Test:** Configure MCP server in extensions_config.json, run skill
**Expected:** User should see "[MCP servers configured: N]" and tool names
**Why human:** Requires real MCP server configuration and observing stderr output
**Current issue:** No MCP status will be logged because skill.py does not call log_mcp_status()

#### 3. MCP Unavailable Warning

**Test:** Configure invalid MCP server in extensions_config.json, run skill
**Expected:** User should see warning "[WARNING] MCP server 'X' enabled but no tools loaded"
**Why human:** Requires misconfigured MCP server and observing warning output
**Current issue:** No warning will appear because skill.py does not call check_mcp_tool_availability()

### Gaps Summary

**Critical Gap: Tool logging functions are orphaned**

All 5 tool registry functions are implemented and tested:
- `log_available_tools()` - TOOL-01
- `get_unique_tool_names()` - TOOL-03
- `get_mcp_tool_names()` - TOOL-02
- `log_mcp_status()` - TOOL-04
- `check_mcp_tool_availability()` - TOOL-05

However, **skill.py does not import or call any of these functions**. This means:
1. Users will NOT see tool names logged at startup
2. Users will NOT see MCP server status
3. Users will NOT be warned about unavailable MCP tools

The functions exist but provide no user-visible benefit because they are not wired into the entry point.

**Required Fix:**
1. Import `lib.tools` in skill.py
2. Call `log_available_tools()` after DeerFlowClient is created
3. Call `log_mcp_status()` with enabled MCP servers
4. Call `check_mcp_tool_availability()` to warn about missing tools

Per RESEARCH.md recommendation: "Call tool logging functions AFTER DeerFlowClient is created, or use get_cached_mcp_tools() which handles lazy initialization"

---

_Verified: 2026-04-27T14:30:00Z_
_Verifier: Claude (gsd-verifier)_
