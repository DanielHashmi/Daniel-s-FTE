---
id: 0003
title: Facebook Composer Lock Fix Validation
stage: green
date: 2026-02-14T15:15:30Z
surface: project
model: gpt-5-codex
feature: dashboard-ui
branch: unknown
user: kk
command: codex
labels: [facebook, playwright, reliability, runtime]
links:
  spec: n/a
  ticket: n/a
  adr: n/a
  pr: n/a
files:
  - path: src/social/facebook_qwen_poster.py
    change: robust_composer_detection_and_login_wait
  - path: src/orchestration/orchestrator.py
    change: approval_retry_backoff
tests:
  - name: py_compile
    result: pass
  - name: create_approve_execute_facebook
    result: pass
---

## Prompt

only browser opened and closed after some moment, i didn't saw my post being posted autonomously

## Response snapshot

Diagnosed runtime logs, identified composer selector and profile-lock failures, patched Facebook posting flow and retry behavior, cleared stale Playwright profile processes, and revalidated with fresh approval execution.

## Outcome

- Impact: Facebook approved posts now execute with resilient composer detection and safer retries.
- Tests: Fresh ID SOCIAL_FACEBOOK_2026-02-14T15-12-12-067Z_1 reached 'Facebook post execution successful' in orchestrator log.
- Files: facebook poster and orchestrator updated.
- Next prompts: optional CDP mode to attach to user’s already-open browser.
- Reflection: failures were from UI selector drift and locked Playwright profile state.

## Evaluation notes (flywheel)

- Failure modes observed: composer not found; launch_persistent_context exitCode 21 profile lock.
- Graders run and results (PASS/FAIL): manual integration checks PASS.
- Prompt variant (if applicable): n/a
- Next experiment (smallest change to try): attach to existing browser via CDP for strict same-browser requirement.
