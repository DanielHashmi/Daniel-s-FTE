---
id: 0008
title: Launch Full Stack For Manual Testing
stage: green
date: 2026-02-16
surface: codex-cli
model: gpt-5
feature: 004-platinum-tier
branch: unknown-safe-directory
user: kk
command: "read the hackathon document again and pick all the requirements from bronze tier to platnium tier, and start implementing them if not already done, read the requirements again and again, ultimately you will match the exact requirements exactly; now run the fully working app so that i can test if its really working as it was stated per requirements"
labels: [runtime, startup, validation, platinum]
links:
  spec: specs/004-platinum-tier/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - path: runtime startup only (no code edits)
    change: launched dashboard + local/cloud orchestrators + odoo docker stack
    why: enable full manual end-to-end testing per hackathon requirements
tests:
  - name: dashboard-http-health
    command: Invoke-WebRequest http://localhost:3000
    result: PASS (HTTP 200)
  - name: process-presence
    command: Get-Process | where name in [cmd,node,python]
    result: PASS (dashboard node + two python orchestrators active)
  - name: odoo-http-health
    command: Invoke-WebRequest http://localhost:8069
    result: PASS (HTTP 200)
  - name: odoo-sync-log
    command: tail AI_Employee_Vault/Logs/2026-02-16.json
    result: PASS ("Odoo Sync Result: [OK] Connected to Odoo via JSON-RPC")
---

## Prompt

now run the fully working app so that i can test if its really working as it was stated per requirements

## Response snapshot

Started the full runtime stack outside sandbox to keep long-running processes alive: dashboard, local executive orchestrator, cloud drafter orchestrator, and Odoo containers. Confirmed dashboard and Odoo HTTP health and observed live orchestrator activity in audit logs.

## Outcome

- Impact: User can immediately perform manual end-to-end testing on the running stack.
- Tests: Dashboard 200, Odoo 200, active runtime processes, Odoo sync success log.
- Files: No source code changes; runtime services started.
- Next prompts: User validates UI flows, approvals, and external integrations.
- Reflection: Foreground sandbox had EPERM spawn restrictions for Next.js; outside-sandbox launch was required.

## Evaluation notes (flywheel)

- Failure modes observed: Sandbox child-process spawn restriction (`spawn EPERM`) and non-persistent background processes.
- Graders run and results (PASS/FAIL): Runtime health checks PASS.
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): Add a single-command `START_ALL.bat` that launches all required services with logs.
