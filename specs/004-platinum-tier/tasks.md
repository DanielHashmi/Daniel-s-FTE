---
title: "Platinum Tier Tasks (Local-First)"
short_name: platinum-tier
feature_number: 004
last_updated: 2026-02-14
---

# Platinum Tier Task List (Aligned With Current Implementation)

This task list reflects what exists in the repo today, plus a small, realistic backlog.

## Completed

- [x] Vault-first workflow folders (`Pending_Approval/`, `Approved/`, `Rejected/`, `Done/`)
- [x] Local orchestrator that processes approvals and writes a heartbeat
- [x] Next.js dashboard for approvals + social drafting
- [x] Facebook post drafting via Qwen CLI invoked with stdin (`-y --input-format text`)
- [x] Facebook posting via Playwright persistent session dir (`FACEBOOK_SESSION_DIR`)
- [x] HITL guarantee: after approval, post EXACTLY approved `## Content` (no regeneration)
- [x] Start scripts for local operator workflow (`START_DASHBOARD.bat`, `START_BRAIN.bat`, `START_ODOO.bat`)
- [x] Docs and specs refreshed to match the repo reality

## Backlog (Quality / Hardening)

- [x] Add `.env.example` and keep it in sync with required env vars
- [ ] Add automated tests: social approval file parsing (`## Content` extraction)
- [ ] Add automated tests: "approved content posts exactly" regression
- [ ] Add env toggles to enable/disable watchers (Gmail/WhatsApp/LinkedIn/Odoo) without code edits
- [ ] Add explicit UI actions for one-time browser session capture (Facebook/LinkedIn/WhatsApp)
- [ ] Improve production hardening: replace default password fallbacks
- [ ] Improve production hardening: add CSRF protection / stricter session handling
