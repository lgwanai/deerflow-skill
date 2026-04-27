---
phase: 04
slug: subagent-delegation
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-04-28
---

# Phase 04 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 7.x |
| **Config file** | pytest.ini |
| **Quick run command** | `pytest tests/ -x -q` |
| **Full suite command** | `pytest tests/ -v --cov=lib --cov=skill --cov-fail-under=80` |
| **Estimated runtime** | ~30 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/ -x -q`
- **After every plan wave:** Run `pytest tests/ -v --cov=lib --cov=skill`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 30 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 04-00-01 | 00 | 0 | SUBA-01, SUBA-02 | unit | `pytest tests/test_subagent.py -x -q` | ❌ W0 | ⬜ pending |
| 04-01-01 | 01 | 1 | SUBA-01 | unit | `pytest tests/test_subagent.py -x -q` | ❌ W0 | ⬜ pending |
| 04-01-02 | 01 | 1 | SUBA-02 | unit | `pytest tests/test_subagent.py -x -q` | ❌ W0 | ⬜ pending |
| 04-01-03 | 01 | 1 | SUBA-04 | unit | `pytest tests/test_subagent.py -x -q` | ❌ W0 | ⬜ pending |
| 04-02-01 | 02 | 1 | SUBA-03 | unit | `pytest tests/test_subagent.py -x -q` | ❌ W0 | ⬜ pending |
| 04-02-02 | 02 | 1 | SUBA-03 | unit | `pytest tests/test_subagent.py -x -q` | ❌ W0 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/test_subagent.py` — stubs for SUBA-01, SUBA-02, SUBA-03, SUBA-04
- [ ] `lib/subagent.py` — module stub (functions return None, no errors)

*Existing infrastructure (pytest, conftest.py from Phase 1) covers test framework.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| Subagent timeout error message visible to user | SUBA-03 | Requires live deerflow-harness with subagent support | Run skill with `--ultra` mode and trigger a subagent timeout, verify error message shows subagent name |

*All other phase behaviors have automated verification.*

---

## Validation Sign-Off

- [ ] All tasks have `<automated>` verify or Wave 0 dependencies
- [ ] Sampling continuity: no 3 consecutive tasks without automated verify
- [ ] Wave 0 covers all MISSING references
- [ ] No watch-mode flags
- [ ] Feedback latency < 30s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
