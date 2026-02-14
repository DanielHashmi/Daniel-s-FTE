# Daniel's FTE (Digital FTE)

Personal AI Employee: a **web dashboard** + a **Python orchestrator ("brain")** that reads/writes an **Obsidian-style vault** (`AI_Employee_Vault/`) and executes **human-approved** actions.

## What You Get

- **Dashboard UI** (`dashboard/`): manage approvals, social drafts, system status.
- **Orchestrator** (`src/orchestration/orchestrator.py`): runs watchers, generates plans, and executes items moved to `AI_Employee_Vault/Approved/`.
- **Human-in-the-loop (HITL)**: sensitive actions (like public posts) require explicit approval before execution.
- **Facebook posting**: generate post copy with **Qwen CLI**, then publish via **Playwright** after approval (posts *exactly* the approved content).

## Project Layout

```
AI_Employee_Vault/                 # Local-first "source of truth" workspace (Obsidian-compatible)
  Pending_Approval/                # Items waiting for human approval
  Approved/                        # Move/approve here to execute
  Rejected/                        # Move/reject here to cancel
  Done/                            # Completed approvals/actions
  Logs/                            # Audit logs + orchestrator heartbeat

dashboard/                         # Next.js web UI (http://localhost:3000)
src/                               # Python brain, watchers, social automation
  orchestration/orchestrator.py
  orchestration/approval_manager.py
  social/facebook_qwen_poster.py

START_DASHBOARD.bat                # Starts the web UI (dev mode)
START_BRAIN.bat                    # Starts the orchestrator brain
START_ODOO.bat                     # Optional: starts local Odoo via Docker
```

## Quick Start (Windows)

### 1) Prereqs

- Node.js (recommended: 20+)
- Python (required by `pyproject.toml`: 3.12+)
- Qwen CLI available on PATH (or set `QWEN_PATH`)
- Playwright browser install (for Facebook automation)

### 2) Install Python deps

```powershell
cd "C:\Users\kk\Desktop\Daniel's FTE"
python -m pip install -e .
python -m playwright install chromium
```

### 3) Configure `.env`

Create/update `.env` in the repo root (it is gitignored). You can start from `.env.example`.

```bash
# Safety first
DRY_RUN=true

# Pick the reasoning engine used for plan generation (qwen or claude)
REASONING_ENGINE=qwen

# Dashboard auth (optional; defaults exist but you should override)
DASHBOARD_PASSWORD=change-me
SESSION_SECRET=change-me-too

# Qwen CLI (optional if qwen is on PATH)
QWEN_PATH=qwen

# Facebook (Qwen + Playwright)
FACEBOOK_COMPOSER_URL=https://www.facebook.com/<your-profile-or-page-composer-url>
FACEBOOK_SESSION_DIR=facebook_session
FACEBOOK_HEADLESS=false
FACEBOOK_LOGIN_WAIT_SECONDS=600
FACEBOOK_KEEP_OPEN_SECONDS=0
# FACEBOOK_BROWSER_CHANNEL=chrome   # optional (e.g. chrome, msedge)
```

Notes:
- Keep `DRY_RUN=true` until you have verified end-to-end behavior.
- `FACEBOOK_COMPOSER_URL` must be a URL where the post composer is available (profile, page, etc.).

### 4) Start the dashboard

Run:

```powershell
START_DASHBOARD.bat
```

Then open `http://localhost:3000`.

Default password fallback (if you did not set `DASHBOARD_PASSWORD`) is printed by `START_DASHBOARD.bat`.

### 5) Start the brain (orchestrator)

In another terminal:

```powershell
START_BRAIN.bat
```

The dashboard detects orchestrator liveness via `AI_Employee_Vault/Logs/orchestrator_heartbeat.json`.

## Facebook Posting (Qwen + Playwright)

### One-time: capture a logged-in session

```powershell
python src/social/facebook_qwen_poster.py --mode login
```

A browser window opens using the persistent session dir (`FACEBOOK_SESSION_DIR`). Log in to Facebook, then press Enter in the terminal to save the session.

### Normal flow (Web UI)

1. Dashboard: create a Facebook post (optionally generate with Qwen, then edit).
2. Click to queue it for approval (creates a file in `AI_Employee_Vault/Pending_Approval/`).
3. Approve it in the dashboard approvals UI (or move the file to `AI_Employee_Vault/Approved/`).
4. The orchestrator posts the approved `## Content` via Playwright.

HITL guarantee: after approval, the system posts **exactly what was approved** (no regeneration after approval).

More details: `docs/facebook-qwen-playwright.md`.

## Odoo (Optional)

This repo includes an optional Odoo workflow (Docker + a local sync skill + approvals).

Start local Odoo:

```powershell
START_ODOO.bat
```

Guide: `docs/guides/odoo-integration-guide.md`.

## Troubleshooting

- Dashboard says brain is offline:
  - Ensure `START_BRAIN.bat` is running and `AI_Employee_Vault/Logs/orchestrator_heartbeat.json` is updating.
- Facebook browser opens then closes without posting:
  - Confirm `DRY_RUN=false` for live posting.
  - Confirm you have a valid session (`--mode login`) and `FACEBOOK_HEADLESS=false` during setup.
  - Set `FACEBOOK_KEEP_OPEN_SECONDS=30` to keep the browser open after clicking Post.
- Qwen not found:
  - Install Qwen CLI and/or set `QWEN_PATH` (Windows often needs `qwen.cmd`).

## Security Notes

- Do not commit secrets: `.env` and session dirs (`facebook_session/`, `linkedin_session/`, `whatsapp_session/`) are ignored by default.
- Public posting is treated as sensitive: keep approvals enabled; use `DRY_RUN=true` during development.
