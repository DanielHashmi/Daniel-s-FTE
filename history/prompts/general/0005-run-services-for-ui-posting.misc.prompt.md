---
id: 0005
title: Run Services For UI Posting
stage: misc
date: 2026-02-14
surface: local-dev
model: gpt-5
feature: facebook-posting-ui
branch: unknown
user: kk
command: Verify dashboard + orchestrator running; improve UI/runtime observability for posting.
labels: [ops, ui, observability]
links:
  spec: ""
  ticket: ""
  adr: ""
  pr: ""
files:
  - path: dashboard/src/app/dashboard/social/page.tsx
    reason: Always show runtime banner and guard Approve & Post Now platform support.
  - path: dashboard/src/app/api/social/accounts/route.ts
    reason: Add orchestrator running fallback via runtime log mtime.
tests:
  - name: Invoke-WebRequest http://localhost:3000
    result: PASS (200)
  - name: Invoke-RestMethod http://localhost:3000/api/social/accounts
    result: PASS (shows orchestrator running=true, dryRun=false)
---

## Prompt

User asked to "run everything yourself" so they only need to create and approve the post via the Web UI.

## Response snapshot

- Confirmed the dashboard is already running on `http://localhost:3000`.
- Confirmed the orchestrator is running (status exposed via `/api/social/accounts`).
- Made the Social page always display DRY_RUN/headless/orchestrator status so the user can immediately verify the system is ready before approving.

## Outcome

- Impact: User can focus on creating/approving posts while the services stay running and the UI clearly indicates readiness.
- Tests: Dashboard reachable; social accounts endpoint returns runtime state.
- Files: Minor UI + API observability improvements.
- Next prompts: If "same browser tab" must mean attaching to an existing Chrome/Edge instance, implement a CDP attach flow with explicit operator consent.
- Reflection: Most user friction was lack of visibility (services running but no obvious signal in UI).

## Evaluation notes (flywheel)

- Failure modes observed: Services not started; DRY_RUN/headless misconfigured; user can't tell if approvals will execute.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add a "Start Brain" and "Start Dashboard" status widget with deep links/instructions.

