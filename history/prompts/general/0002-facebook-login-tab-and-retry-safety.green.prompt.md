---
id: 0002
title: Facebook Login Tab Retry Safety
stage: green
date: 2026-02-14T14:59:00Z
surface: project
model: gpt-5-codex
feature: dashboard-ui
branch: unknown
user: kk
command: codex
labels: [facebook, playwright, approvals, runtime]
links:
  spec: n/a
  ticket: n/a
  adr: n/a
  pr: n/a
files:
  - path: src/social/facebook_qwen_poster.py
    change: keep_login_tab_open_and_new_tab_behavior
  - path: src/orchestration/approval_manager.py
    change: return_success_flags
  - path: src/orchestration/orchestrator.py
    change: keep_failed_approved_items_for_retry
tests:
  - name: python_compile
    result: pass
  - name: runtime_restart
    result: pass
---

## Prompt

first of all, open facebook in the same browser, in a new tab, and right now it opens new broswer and shows login page of facebook then automatically closes the broswer, that's it

## Response snapshot

Updated Facebook Playwright flow to always use a new tab, wait for manual login before failing, and avoid moving failed approvals to Done. Opened Facebook in default browser new tab for immediate login.

## Outcome

- Impact: Login page no longer closes immediately; approvals are retry-safe.
- Tests: py_compile pass; orchestrator restarted with new behavior.
- Files: facebook poster, approval manager, orchestrator updated.
- Next prompts: validate one live approval after manual Facebook login.
- Reflection: failure path handling was the key issue, not generation logic.

## Evaluation notes (flywheel)

- Failure modes observed: login redirect triggered immediate close; failed approvals archived as done.
- Graders run and results (PASS/FAIL): manual integration checks PASS.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): optional CDP attach mode for true existing-browser control.
