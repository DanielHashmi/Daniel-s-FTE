# Facebook: Qwen + Playwright Automation

This feature lets the Digital FTE:
- Generate Facebook post copy with **Qwen CLI**
- Queue posts for **human approval** from the **web UI**
- Publish approved posts via **Playwright** browser automation

## How It Works (HITL Guarantee)

1. The web UI creates an approval file in `AI_Employee_Vault/Pending_Approval/` containing:
   - YAML frontmatter (`platform: facebook`, `brain: qwen`, optional `qwen_prompt`)
   - `## Content` (the exact text to be posted)
2. A human approves by moving the file to `AI_Employee_Vault/Approved/` (or via the dashboard approvals UI).
3. The orchestrator detects the approved file and runs Playwright automation.

Important: after approval, the system posts **exactly** the approved `## Content`. It does not re-run Qwen after approval.

## Required Environment Variables

Set these in the repo root `.env` (gitignored):

```bash
# Safety first (recommended while validating setup)
DRY_RUN=true

# Qwen CLI
REASONING_ENGINE=qwen
QWEN_PATH=qwen            # Windows often needs qwen.cmd
QWEN_TIMEOUT_SECONDS=120  # optional

# Facebook (Playwright)
FACEBOOK_COMPOSER_URL=https://www.facebook.com/<your-profile-or-page-composer-url>
FACEBOOK_SESSION_DIR=facebook_session
FACEBOOK_HEADLESS=false
FACEBOOK_LOGIN_WAIT_SECONDS=600
FACEBOOK_KEEP_OPEN_SECONDS=0
# FACEBOOK_BROWSER_CHANNEL=chrome   # optional (e.g. chrome, msedge)
```

Notes:
- With `DRY_RUN=true`, the Facebook poster will **not open a browser** and will not publish anything live.
- `FACEBOOK_COMPOSER_URL` must be a URL where the post composer is available for your target (profile/page).

## One-Time Setup: Capture Facebook Session

Run:

```bash
python src/social/facebook_qwen_poster.py --mode login
```

A persistent browser window opens using `FACEBOOK_SESSION_DIR`. Log in manually, then press Enter in the terminal to save the session.

## Web UI Flow

1. Open the dashboard Social page.
2. Generate post text with Qwen (optional) and edit as needed.
3. Queue it for approval (writes an approval file to `Pending_Approval/`).
4. Approve it (moves to `Approved/`).
5. The orchestrator posts it via Playwright.

### How Qwen Is Used In The Web UI

When you click "Generate with Qwen", the dashboard calls `POST /api/social/facebook/generate` which:
- Builds a strict prompt (`dashboard/src/lib/qwen.ts`)
- Spawns Qwen with:

```bash
qwen -y --input-format text
```

- Passes the prompt on **stdin** (no `-p`), then normalizes output into plain post text.

## Orchestrator Execution Path

On approval, the orchestrator uses `src/orchestration/approval_manager.py` to execute:
- `python src/social/facebook_qwen_poster.py --mode post --content "<approved content>" --json`
  - Adds `--dry-run` if `DRY_RUN=true`
  - Adds `--headless` if `FACEBOOK_HEADLESS=true`

If (and only if) the approval file contains no `## Content`, it may run:
- `python src/social/facebook_qwen_poster.py --mode generate-and-post --prompt "<qwen_prompt>" --json`

## Troubleshooting

- Browser opens Facebook login then closes:
  - Your session is not logged in. Run `--mode login` with `FACEBOOK_HEADLESS=false` and complete login.
  - Increase `FACEBOOK_LOGIN_WAIT_SECONDS` to give yourself more time.
- You want to see the browser stay open after clicking Post:
  - Set `FACEBOOK_KEEP_OPEN_SECONDS=30` (and ensure `FACEBOOK_HEADLESS=false`).
- It fails to find the composer textbox:
  - A screenshot is saved under `FACEBOOK_SESSION_DIR/debug_screenshots/`.
