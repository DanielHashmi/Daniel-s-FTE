# Demo Video Script (Local-First Digital FTE)

**Goal**: Demonstrate the real, current workflow in this repo: dashboard-managed approvals + local orchestrator execution + Facebook posting (Qwen + Playwright) with HITL.

## Act I: Setup (0:00-1:00)

1. Show repo structure:
   - `AI_Employee_Vault/`
   - `dashboard/`
   - `src/orchestration/orchestrator.py`
   - `src/social/facebook_qwen_poster.py`
2. Start the dashboard:
   ```powershell
   START_DASHBOARD.bat
   ```
3. Start the orchestrator:
   ```powershell
   START_BRAIN.bat
   ```
4. Open `http://localhost:3000` and log in.

## Act II: HITL Approval Loop (1:00-2:30)

1. Open dashboard Approvals view.
2. Explain the vault-based state machine:
   - `Pending_Approval/` -> `Approved/` or `Rejected/` -> `Done/`
3. Show orchestrator heartbeat file:
   - `AI_Employee_Vault/Logs/orchestrator_heartbeat.json`

## Act III: Facebook Posting (Qwen + Playwright) (2:30-5:30)

### One-time setup (if needed)

1. Capture a logged-in Facebook session:
   ```powershell
   python src/social/facebook_qwen_poster.py --mode login
   ```
2. Login in the opened browser window and press Enter in the terminal.

### Demo flow

1. In the dashboard Social page:
   - Enter a prompt
   - Click "Generate with Qwen"
   - Edit the post text (optional)
2. Queue for approval (creates a file in `AI_Employee_Vault/Pending_Approval/`).
3. Approve the post in the dashboard.
4. Narrate the core guarantee:
   - After approval, the orchestrator posts EXACTLY the approved `## Content`.
5. Show the browser automation (live mode):
   - Set `DRY_RUN=false`
   - Optionally set `FACEBOOK_KEEP_OPEN_SECONDS=30` to keep the browser open briefly after clicking Post

## Act IV: Observability / Audit (5:30-6:30)

1. Show that the approval file moved to `AI_Employee_Vault/Done/`.
2. Show an audit log entry in:
   - `AI_Employee_Vault/Logs/YYYY-MM-DD.json`

## Act V: Optional Odoo Approval (6:30-7:30)

1. Start Odoo:
   ```powershell
   START_ODOO.bat
   ```
2. Run a sync:
   ```powershell
   python .claude/skills/odoo-accounting/scripts/main_operation.py sync
   ```
3. Show an approval file example created when posting invoices in live mode:
   - `AI_Employee_Vault/Pending_Approval/invoice_<ID>_approval.yaml`

## Wrap-Up (7:30-8:00)

- Local-first: vault is the control plane
- HITL by default for sensitive actions
- Qwen + Playwright provide real autonomous social posting (after approval)

