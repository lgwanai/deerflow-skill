---
phase: 3
slug: tool-registry-exposure
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-27
---

# Phase 3 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | `pyproject.toml` |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v --cov=lib --cov-report=term-missing` |
| **Estimated runtime** | ~15 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v --cov=lib --cov-report=term-missing`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 20 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 03-01-01 | 01 | 1 | TOOL-01 | unit | `pytest tests/test_tool_registry.py -k test_builtin_tools -v` | ❌ W0 | ⬜ pending |
| 03-01-02 | 01 | 1 | TOOL-03 | unit | `pytest tests/test_tool_registry.py -k test_tool_logging -v` | ❌ W0 | ⬜ pending |
| 03-02-01 | 02 | 2 | TOOL-02 | unit | `pytest tests/test_tool_registry.py -k test_mcp_tools -v` | ❌ W0 | ⬜ pending |
| 03-02-02 | 02 | 2 | TOOL-04 | unit | `pytest tests/test_tool_registry.py -k test_mcp_success_log -v` | ❌ W0 | ⬜ pending |
| 03-02-03 | 02 | 2 | TOOL-05 | unit | `pytest tests/test_tool_registry.py -k test_mcp_warning -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_tool_registry.py` — stubs for TOOL-01, TOOL-02, TOOL-03, TOOL-04, TOOL-05
- [ ] `tests/conftest.py` — fixtures for mock tool registry, MCP client

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| MCP tool loading log visibility | TOOL-04 | Subjective UX clarity | Run skill with MCP config, observe tool loading output |
| MCP unavailable warning clarity | TOOL-05 | Human judgment | Configure invalid MCP server, verify warning is actionable |

*If none: "All phase behaviors have automated verification."*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 20s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending