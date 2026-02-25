---
id: 0007
title: Refresh README, Docs, And Specs
stage: misc
date: 2026-02-14
surface: repo-docs
model: gpt-5
feature: docs-and-specs-refresh
branch: unknown
user: kk
command: Create an accurate root README, update docs to match implementation, and refresh stale specs/004-platinum-tier documents while respecting each file's purpose.
labels: [docs, specs, readme, facebook, qwen, playwright, hitl]
links:
  spec: "specs/004-platinum-tier/spec.md"
  ticket: ""
  adr: ""
  pr: ""
files:
  - path: README.md
    reason: Add an accurate root README for current local-first dashboard + brain + vault workflow and Facebook Qwen/Playwright flow.
  - path: .env.example
    reason: Provide a safe, commit-friendly template of required env vars (no real secrets).
  - path: START_BRAIN.bat
    reason: Fix the startup banner so it no longer claims "no approvals" and matches HITL behavior.
  - path: docs/README.md
    reason: Add a docs index for discoverability.
  - path: docs/facebook-qwen-playwright.md
    reason: Update to reflect current Qwen stdin invocation, HITL guarantee, and exact approved content posting.
  - path: docs/guides/odoo-integration-guide.md
    reason: Update to match the current local Odoo + skill-based integration and approval flow; remove stale WSL assumptions.
  - path: docs/demo-video-script.md
    reason: Replace the stale cloud/local demo script with a local-first demo that matches the repo behavior.
  - path: docs/demo_script.md
    reason: Replace the stale demo outline with the current local-first workflow.
  - path: specs/004-platinum-tier/spec.md
    reason: Rewrite the stale cloud/local specification to reflect the repo's current local-first Platinum Tier reality.
  - path: specs/004-platinum-tier/plan.md
    reason: Update the plan to document the actual architecture and execution path used in the repo.
  - path: specs/004-platinum-tier/tasks.md
    reason: Replace duplicated/inconsistent tasks with a clean "completed vs backlog" list aligned to the repo.
  - path: specs/004-platinum-tier/quickstart.md
    reason: Update operator quickstart steps for running dashboard + brain + Facebook session capture locally.
  - path: specs/004-platinum-tier/data-model.md
    reason: Document the current vault approval artifacts, heartbeat, and audit log formats.
  - path: specs/004-platinum-tier/research.md
    reason: Refresh research notes to match the current local-first decisions (Qwen stdin, Playwright persistent context, heartbeat).
  - path: specs/004-platinum-tier/checklists/requirements.md
    reason: Refresh the spec quality checklist to reference the updated local-first spec.
  - path: specs/004-platinum-tier/contracts/mcp-sync.yaml
    reason: Mark the prior sync contract as legacy/not used by the current implementation to avoid confusion.
  - path: AI_Employee_Vault/README.md
    reason: Remove stale tier labeling in the vault README.
tests:
  - name: N/A
    result: Not run (docs/spec refresh only)
---

## Prompt

User requested:
- Create a proper accurate root README.md
- Update docs based on the actual implementation
- Update stale specs documents to reflect the actual project, while preserving each file's purpose

## Response snapshot

- Added a new root `README.md` describing the current local-first architecture (dashboard + orchestrator + vault) and the Facebook Qwen + Playwright HITL flow.
- Updated/added docs to match actual behavior, including Qwen stdin invocation and the "post exactly approved content" guarantee.
- Rewrote `specs/004-platinum-tier/*` to describe the current repo reality instead of the older cloud/local sync plan.
- Added `.env.example` as a safe template and corrected misleading startup messaging.

## Outcome

- Impact: Documentation and specs now describe the system as it actually runs today, reducing operator confusion and mismatched expectations.
- Tests: Not run (documentation/specification changes only).
- Files: Added root README, refreshed Facebook/Odoo docs, updated Platinum Tier specs (spec/plan/tasks/quickstart/data-model/research).
- Next prompts: If desired, add tests for approval parsing and a UI flow to capture browser sessions (Facebook/LinkedIn/WhatsApp).
- Reflection: In HITL systems, docs must be explicit about what is executed from the approved artifact to preserve trust and auditability.

## Evaluation notes (flywheel)

- Failure modes observed: stale docs/specs described cloud/local sync that is not the current primary execution model.
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add regression tests for "approved content is posted verbatim" to prevent future drift.

