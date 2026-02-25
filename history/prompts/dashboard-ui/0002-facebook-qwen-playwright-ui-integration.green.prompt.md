---
id: 0002
title: "Facebook Qwen Playwright UI integration"
stage: green
date: 2026-02-14
surface: CLI
model: gpt-5-codex
feature: dashboard-ui
branch: dashboard-ui
user: KK
command: "add facebook posting via playwright managed through web ui and qwen brain"
labels: [facebook, qwen, playwright, dashboard, approvals]
links:
  spec: "specs/004-platinum-tier/spec.md"
  ticket: "N/A"
  adr: "N/A"
  pr: "N/A"
files:
  - path: "src/social/facebook_qwen_poster.py"
    action: "created"
  - path: "src/orchestration/approval_manager.py"
    action: "modified"
  - path: "dashboard/src/lib/qwen.ts"
    action: "created"
  - path: "dashboard/src/app/api/social/accounts/route.ts"
    action: "created"
  - path: "dashboard/src/app/api/social/facebook/generate/route.ts"
    action: "created"
  - path: "dashboard/src/app/api/social/post/route.ts"
    action: "modified"
  - path: "dashboard/src/app/api/social/posts/route.ts"
    action: "modified"
  - path: "dashboard/src/app/dashboard/social/page.tsx"
    action: "modified"
  - path: "dashboard/src/app/api/settings/route.ts"
    action: "modified"
  - path: "tests/unit/test_facebook_qwen_poster.py"
    action: "created"
  - path: "docs/facebook-qwen-playwright.md"
    action: "created"
  - path: ".gitignore"
    action: "modified"
  - path: "pyproject.toml"
    action: "modified"
tests:
  - path: "tests/unit/test_facebook_qwen_poster.py"
    status: "pass (4 tests)"
  - path: "python -m compileall src/social/facebook_qwen_poster.py src/orchestration/approval_manager.py"
    status: "pass"
  - path: "dashboard lint (changed files only)"
    status: "pass"
---

## Prompt

User requested Facebook management capability through the web UI, enforced Qwen-only brain behavior, and automated terminal command execution for Qwen + posting workflows.

## Response snapshot

Implemented end-to-end Facebook automation:
- Qwen generation pipeline with CLI subprocess execution.
- Playwright Facebook posting executor with dry-run and session-login mode.
- ApprovalManager integration to run approved Facebook jobs through Qwen + Playwright.
- Dashboard APIs for social accounts and Facebook Qwen generation.
- Social UI updates for platform readiness, prompt entry, Qwen generation, and approval queueing.
- Added focused unit tests and setup documentation.

## Outcome

- Impact: FTE can now generate and execute Facebook posting workflows via Qwen + Playwright from web-managed flows.
- Tests: Added and passed new unit tests; compile checks and changed-file lint checks passed.
- Files: Added backend automation module, dashboard routes/lib, UI updates, docs, and tests.
- Next prompts: Enable and validate live posting by setting `FACEBOOK_COMPOSER_URL` and capturing session.
- Reflection: Approval-gated execution preserved HITL while adding autonomous Qwen generation.

## Evaluation notes (flywheel)

- Failure modes observed: missing Facebook session / missing Qwen CLI path cause explicit execution errors.
- Graders run and results (PASS/FAIL): PASS for targeted checks.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): add a UI action to trigger `--mode login` session bootstrap safely.
