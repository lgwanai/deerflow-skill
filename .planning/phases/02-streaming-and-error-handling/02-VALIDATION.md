---
phase: 2
slug: streaming-and-error-handling
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-27
---

# Phase 2 — Validation Strategy

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
| 02-01-01 | 01 | 1 | STRM-01 | unit | `pytest tests/test_stream.py -k test_token_streaming -v` | ❌ W0 | ⬜ pending |
| 02-01-02 | 01 | 1 | STRM-02 | unit | `pytest tests/test_stream.py -k test_tool_progress -v` | ❌ W0 | ⬜ pending |
| 02-01-03 | 01 | 1 | STRM-03 | unit | `pytest tests/test_stream.py -k test_custom_events -v` | ❌ W0 | ⬜ pending |
| 02-01-04 | 01 | 1 | STRM-04 | unit | `pytest tests/test_stream.py -k test_end_event -v` | ❌ W0 | ⬜ pending |
| 02-02-01 | 02 | 1 | ERRR-01 | unit | `pytest tests/test_errors.py -k test_recursion_limit -v` | ❌ W0 | ⬜ pending |
| 02-02-02 | 02 | 1 | ERRR-02 | unit | `pytest tests/test_errors.py -k test_llm_provider_errors -v` | ❌ W0 | ⬜ pending |
| 02-02-03 | 02 | 1 | ERRR-03 | unit | `pytest tests/test_errors.py -k test_stateless_sessions -v` | ❌ W0 | ⬜ pending |
| 02-02-04 | 02 | 1 | ERRR-04 | unit | `pytest tests/test_errors.py -k test_actionable_guidance -v` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_stream.py` — stubs for STRM-01, STRM-02, STRM-03, STRM-04
- [ ] `tests/test_errors.py` — stubs for ERRR-01, ERRR-02, ERRR-03, ERRR-04
- [ ] `tests/conftest.py` — fixtures for mock DeerFlowClient, StreamEvent

*If none: "Existing infrastructure covers all phase requirements."*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Real-time token visibility | STRM-01 | Subjective UX timing | Run skill in interactive mode, observe tokens appearing one-by-one |
| Error message clarity | ERRR-04 | Human judgment | Force various error conditions, verify messages are actionable |

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
