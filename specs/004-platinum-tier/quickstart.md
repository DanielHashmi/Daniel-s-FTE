# Platinum Tier Quickstart (Local-First)

This quickstart matches the repo's current primary workflow: run the dashboard + orchestrator locally and approve sensitive actions before execution.

## 1) Prerequisites

- Node.js 20+
- Python 3.12+
- Qwen CLI available (`qwen` / `qwen.cmd`)
- Playwright installed + Chromium downloaded

## 2) Install Dependencies

```powershell
cd "C:\Users\kk\Desktop\Daniel's FTE"

# Python deps
python -m pip install -e .
python -m playwright install chromium

# Dashboard deps (optional: START_DASHBOARD.bat installs automatically)
cd dashboard
npm install
```

## 3) Configure `.env`

Create/update `.env` in the repo root:

```bash
DRY_RUN=true
REASONING_ENGINE=qwen
QWEN_PATH=qwen

DASHBOARD_PASSWORD=change-me
SESSION_SECRET=change-me-too

FACEBOOK_COMPOSER_URL=https://www.facebook.com/<your-profile-or-page-composer-url>
FACEBOOK_SESSION_DIR=facebook_session
FACEBOOK_HEADLESS=false
FACEBOOK_LOGIN_WAIT_SECONDS=600
FACEBOOK_KEEP_OPEN_SECONDS=0
```

## 4) Start Services

Terminal 1:
```powershell
START_DASHBOARD.bat
```

Terminal 2:
```powershell
START_BRAIN.bat
```

Open `http://localhost:3000` and log in.

## 5) One-Time Facebook Login Session

```powershell
python src/social/facebook_qwen_poster.py --mode login
```

Log in in the opened browser window, then press Enter in the terminal.

## 6) Create + Approve + Post

1. Create a Facebook post in the dashboard Social UI (generate with Qwen if desired).
2. Queue for approval (creates a file in `AI_Employee_Vault/Pending_Approval/`).
3. Approve in the dashboard (moves the file to `AI_Employee_Vault/Approved/`).
4. Orchestrator posts the approved content and moves the file to `AI_Employee_Vault/Done/`.

## Optional: Start Odoo

```powershell
START_ODOO.bat
```

See `docs/guides/odoo-integration-guide.md`.

