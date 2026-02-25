---
id: 0004
title: Web UI Approve And Post
stage: green
date: 2026-02-14
surface: dashboard
model: gpt-5
feature: facebook-posting-ui
branch: unknown
user: kk
command: Add "Approve & Post Now" flow, runtime status indicators, and more robust Facebook login detection.
labels: [ui, facebook, playwright, approvals, reliability]
links:
  spec: ""
  ticket: ""
  adr: ""
  pr: ""
files:
  - path: dashboard/src/app/dashboard/social/page.tsx
    reason: Add "Approve & Post Now" and show dry-run/headless/orchestrator status in the UI.
  - path: dashboard/src/app/api/social/accounts/route.ts
    reason: Return runtime config (dry-run/headless/keep-open/channel) and orchestrator running signal (heartbeat/log fallback).
  - path: dashboard/src/app/dashboard/approvals/page.tsx
    reason: Improve Facebook approval messaging and fix non-ASCII UI glyphs; include platform/action fields.
  - path: src/orchestration/orchestrator.py
    reason: Write orchestrator heartbeat file for UI health detection.
  - path: src/social/facebook_qwen_poster.py
    reason: Detect Facebook login reliably (URL or form) and support launching installed browser via channel.
  - path: START_BRAIN.bat
    reason: Prefer a local pythoncore runtime when `python` is not on PATH.
tests:
  - name: npm -C dashboard run lint
    result: FAIL (pre-existing lint errors in unrelated files)
  - name: Invoke-RestMethod http://localhost:3000/api/social/accounts
    result: PASS
---

## Prompt

User expected Facebook to visibly open and post when triggering from the Web UI, but saw nothing (or a browser briefly open/close on the Facebook login page). User asked for Facebook to open in the same browser/new tab, and asked for the dashboard password.

## Response snapshot

- Added an "Approve & Post Now" button in the Social UI that creates the post then immediately approves it, so posting starts without a separate Approvals step.
- Surfaced runtime status in the UI (DRY_RUN, Facebook headless/keep-open seconds/browser channel, and whether the orchestrator appears to be running).
- Improved Facebook login detection so the automation does not immediately close when Facebook serves a login form on a non-/login URL.
- Added an orchestrator heartbeat file and a log-mtime fallback so the dashboard can detect if the orchestrator is active.

## Outcome

- Impact: Web UI posting now gives immediate, visible feedback and can trigger execution in one step; Facebook login handling is less fragile.
- Tests: Dashboard lint still fails due to unrelated existing issues; social accounts endpoint verified live.
- Files: Updated UI + API runtime status + orchestrator heartbeat + Facebook automation reliability.
- Next prompts: Consider adding a CDP attach mode if "same browser window/tab" must literally mean an already-open Chrome/Edge instance.
- Reflection: The main failure was user expectation mismatch (queued vs executed) and poor observability; adding explicit runtime indicators + one-click approval reduces confusion.

## Evaluation notes (flywheel)

- Failure modes observed: Orchestrator not running; DRY_RUN/headless enabled; Facebook login served without /login URL; user could not tell whether anything executed.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add a small "Prepare Facebook Session" action in the UI that opens the persistent profile for login and keeps it open for a configurable period.

