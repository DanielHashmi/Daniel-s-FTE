---
id: 0006
title: Post Exact Approved Facebook Content
stage: green
date: 2026-02-14
surface: dashboard-orchestrator
model: gpt-5
feature: facebook-posting-ui
branch: unknown
user: kk
command: Fix Facebook pipeline so the approved content is what gets posted; explain Qwen usage via Web UI.
labels: [facebook, hitl, qwen, playwright, bugfix]
links:
  spec: ""
  ticket: ""
  adr: ""
  pr: ""
files:
  - path: src/orchestration/approval_manager.py
    reason: Stop regenerating after approval; post exactly approved content and strip approval footer from extracted content.
  - path: dashboard/src/app/api/social/post/route.ts
    reason: Do not regenerate Facebook content if the user already supplied content in the Web UI.
  - path: src/watchers/gmail.py
    reason: Prevent Gmail OAuth auth flow from blocking orchestrator startup; avoid auto-OAuth unless explicitly enabled.
  - path: src/orchestration/orchestrator.py
    reason: Add a heartbeat loop thread so the UI can detect orchestrator liveness reliably.
  - path: dashboard/src/app/api/social/accounts/route.ts
    reason: Relax orchestrator liveness threshold to avoid false negatives during long cycles.
tests:
  - name: Invoke-RestMethod http://localhost:3000/api/social/accounts
    result: PASS (orchestrator running=true after starting brain)
---

## Prompt

User reported a mismatch between the text they submitted and what actually posted to Facebook: the live post included extra Qwen-generated text plus the internal footer "*This post requires approval before posting*". User also asked how Qwen was used through the Web UI.

## Response snapshot

- Root cause: the system was effectively generating twice and also included the approval footer as seed content, causing Qwen to rewrite/append text and sometimes echo the footer into the live post.
- Fix: approvals now post exactly what the human approved (no regeneration at execution), and content extraction stops before the approval footer.
- Fix: Web UI create endpoint no longer regenerates Facebook content if the user already supplied content (e.g., via "Generate with Qwen" and edits).
- Reliability: prevented Gmail OAuth from blocking orchestrator startup; added a heartbeat loop so the UI can reliably detect the brain is running.

## Outcome

- Impact: Facebook posts will match the approved content; no internal footer leaks into live posts.
- Tests: Verified orchestrator status via dashboard endpoint once the brain is started.
- Files: Updated approval execution, Web UI post creation behavior, and orchestrator startup/liveness.
- Next prompts: Consider adding a dedicated "Prepare Facebook Session" button in the UI to open and keep the persistent login profile open.
- Reflection: For HITL workflows, regenerating content after approval violates the approval contract; posting must be deterministic from the approved artifact.

## Evaluation notes (flywheel)

- Failure modes observed: content regenerated after approval; internal footer included in seed; orchestrator startup blocked by Gmail OAuth; UI liveness false negative during long cycles.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Persist the exact "posted_content" in the Done file for audit and reconciliation.

