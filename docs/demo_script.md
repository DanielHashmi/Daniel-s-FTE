# Demo Script (Local-First Digital FTE)

## 1) Start Services

```powershell
START_DASHBOARD.bat
START_BRAIN.bat
```

Open `http://localhost:3000` and log in.

## 2) Show HITL Approval Folders

- `AI_Employee_Vault/Pending_Approval/`
- `AI_Employee_Vault/Approved/`
- `AI_Employee_Vault/Rejected/`
- `AI_Employee_Vault/Done/`

Show heartbeat:
- `AI_Employee_Vault/Logs/orchestrator_heartbeat.json`

## 3) Facebook Posting (Qwen + Playwright)

One-time session capture (if needed):
```powershell
python src/social/facebook_qwen_poster.py --mode login
```

Demo flow:
1. Dashboard Social page: generate with Qwen, edit, queue for approval.
2. Approve in the dashboard.
3. Orchestrator posts the approved `## Content` (no regeneration after approval).

## 4) Audit Trail

Show:
- `AI_Employee_Vault/Logs/YYYY-MM-DD.json`

