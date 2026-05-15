---
phase: 1
slug: core-integration
status: draft
nyquist_compliant: true
wave_0_complete: false
created: 2026-04-27
---

# Phase 1 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 8.0+ |
| **Config file** | pyproject.toml [tool.pytest.ini_options] |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v --cov=lib` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v --cov=lib`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 01-01-01 | 01 | 1 | CORE-01, CONF-04 | unit | `pytest tests/test_imports.py -x` | ❌ W0 | ⬜ pending |
| 01-01-02 | 01 | 1 | CONF-03 | unit | `pytest tests/test_errors.py::test_missing_config_error -x` | ❌ W0 | ⬜ pending |
| 01-02-01 | 02 | 1 | CONF-01, CONF-02, CORE-02 | unit | `pytest tests/test_config.py -x` | ❌ W0 | ⬜ pending |
| 01-02-02 | 02 | 1 | CORE-03, LLM-04 | unit | `pytest tests/test_config.py::test_credentials_present -x` | ❌ W0 | ⬜ pending |
| 01-03-01 | 03 | 1 | CORE-04, CORE-05 | integration | `pytest tests/test_client.py -x` | ❌ W0 | ⬜ pending |
| 01-03-02 | 03 | 1 | LLM-01, LLM-02, LLM-03 | integration | `pytest tests/test_models.py -x` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_imports.py` — verifies deerflow-harness importable (CORE-01, CONF-04)
- [ ] `tests/test_config.py` — config resolution and validation (CONF-01, CONF-02, CORE-02, CORE-03)
- [ ] `tests/test_errors.py` — error message formatting (CONF-03)
- [ ] `tests/test_modes.py` — mode preset mapping (user decisions)
- [ ] `tests/test_client.py` — DeerFlowClient creation and chat (CORE-04, CORE-05)
- [ ] `tests/test_models.py` — multi-provider model support (LLM-01, LLM-02, LLM-03)
- [ ] `tests/conftest.py` — shared fixtures (mock config, mock client)

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| SKILL.md invocation in Claude Code | CORE-01 | Claude Code skill format needs real environment | Run `/deer-flow "test"` in Claude Code session |
| config.example.yaml creation | CONF-03 | File creation needs file system state | Run skill without config.yaml, verify template created |

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending