---
title: "Platinum Tier Tasks (Hackathon 0)"
short_name: platinum-tier
feature_number: 004
last_updated: 2026-02-15
---

# Platinum Tier Task List (Hackathon 0 Compliance)

This task list tracks implementation against the full Hackathon 0 Platinum requirements.

## Completed

- [x] Vault-first workflow folders (`Pending_Approval/`, `Approved/`, `Rejected/`, `Done/`)
- [x] Local orchestrator that processes approvals and writes a heartbeat
- [x] Cloud orchestrator role (`AGENT_ROLE=cloud`) with draft-only behavior
- [x] Strict cloud/local work-zone ownership gate (`STRICT_WORK_ZONES`)
- [x] Claim-by-move ownership queue via `In_Progress/<agent>/`
- [x] Next.js dashboard for approvals + social drafting
- [x] Domain-aware approval APIs and recursive vault traversal in dashboard routes
- [x] Facebook post drafting via Qwen CLI invoked with stdin (`-y --input-format text`)
- [x] Facebook posting via Playwright persistent session dir (`FACEBOOK_SESSION_DIR`)
- [x] HITL guarantee: after approval, post EXACTLY approved `## Content` (no regeneration)
- [x] MCP action execution paths for email/social/Odoo approval handlers
- [x] Cloud Odoo deployment artifacts (compose + HTTPS proxy + backup + healthcheck)
- [x] PM2 manager skill updated for local/cloud/dashboard apps
- [x] Start scripts for local operator workflow (`START_DASHBOARD.bat`, `START_BRAIN.bat`, `START_ODOO.bat`)
- [x] Platinum demo validator (`scripts/platinum_demo_gate.py`)
- [x] Docs and specs refreshed for hackathon requirement mapping

## Backlog (Quality / Hardening)

- [x] Add `.env.example` and keep it in sync with required env vars
- [x] Add automated tests: social approval file parsing (`## Content` extraction)
- [x] Add automated tests: "approved content posts exactly" regression
- [x] Add env toggles to enable/disable watchers (Gmail/WhatsApp/LinkedIn/Odoo) without code edits
- [ ] Add explicit UI actions for one-time browser session capture (Facebook/LinkedIn/WhatsApp)
- [ ] Improve production hardening: replace default password fallbacks
- [ ] Improve production hardening: add CSRF protection / stricter session handling
