---
id: 0001
title: Run Facebook Feature Runtime
stage: green
date: 2026-02-14T14:21:00Z
surface: project
model: gpt-5-codex
feature: dashboard-ui
branch: unknown
user: kk
command: codex
labels: [runtime, facebook, qwen, orchestrator]
links:
  spec: n/a
  ticket: n/a
  adr: n/a
  pr: n/a
files:
  - path: dashboard/src/lib/qwen.ts
    change: fix_windows_cmd_spawn
  - path: src/orchestration/orchestrator.py
    change: prioritize_approvals_and_safe_moves
tests:
  - name: social-post-flow
    result: pass
  - name: approval-execution-flow
    result: pass
---

## Prompt

run the fully working app, so that i can test this feature

## Response snapshot

Started dashboard and orchestrator, fixed Windows qwen spawn, fixed approval queue blocking, restarted services, and verified create/approve/execute flow for Facebook with Qwen + Playwright.

## Outcome

- Impact: Facebook approval execution now completes through orchestrator.
- Tests: API login, social post creation, approval, and Done-folder completion passed.
- Files: qwen spawn and orchestrator cycle handling updated.
- Next prompts: optionally clean legacy Approved items and disable unused watchers for quieter runtime.
- Reflection: runtime failures were due process duplication and queue error handling, not core Facebook feature logic.

## Evaluation notes (flywheel)

- Failure modes observed: duplicate orchestrators, Done-file collision in approvals, Ralph wrapper signature mismatch.
- Graders run and results (PASS/FAIL): manual integration checks PASS.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): isolate social execution from non-social watcher failures.
