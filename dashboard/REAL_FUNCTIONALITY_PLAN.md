# Dashboard Real Functionality Implementation Plan

## Objective
Convert the static dashboard to fully functional interface that controls the actual AI Employee system.

## Real Backend Integration Points

### 1. FTE Control (`/api/fte/`)
- **GET /api/fte/status**
  - Read `.fte_status` file from AI_Employee_Vault
  - Check running Python processes (orchestrator, watchers)
  - Return real service status
  
- **POST /api/fte/start**
  - Execute `python src/orchestration/orchestrator.py` as background process
  - Write `running` to `.fte_status`
  - Start watchers via PM2 or directly

- **POST /api/fte/stop**
  - Kill orchestrator and watcher processes
  - Write `stopped` to `.fte_status`

### 2. Approvals (`/api/approvals/`)
- **GET /api/approvals**
  - Read all `.md` files from `AI_Employee_Vault/Pending_Approval/`
  - Parse frontmatter and content
  - Return structured list

- **POST /api/approvals/[id]/approve**
  - Move file from `Pending_Approval/` to `Approved/`
  - Create signal file in `Signals/` folder for orchestrator

- **POST /api/approvals/[id]/reject**
  - Move file from `Pending_Approval/` to `Rejected/`

### 3. Social Media (`/api/social/`)
- **POST /api/social/post**
  - Create markdown file in `Pending_Approval/` with post content
  - Use frontmatter format with platform, content, status

- **GET /api/social/posts**
  - Read from `Pending_Approval/`, `Approved/`, and `Done/` folders
  - Filter social media posts
  - Return with status (pending/approved/posted)

### 4. Email (`/api/email/`)
- **GET /api/email/inbox**
  - Read from `AI_Employee_Vault/Needs_Action/` for emails needing action
  - Read from `Pending_Approval/` for draft emails
  - Parse and return

### 5. Logs (`/api/logs`)
- **GET /api/logs**
  - Read from `AI_Employee_Vault/Logs/` directory
  - Parse recent log entries
  - Return with level, timestamp, message

### 6. Settings (`/api/settings`)
- **GET /api/settings**
  - Read `.env` file
  - Parse DRY_RUN, REQUIRE_*_APPROVAL flags
  - Check integration credentials existence

- **PATCH /api/settings**
  - Update specific .env variables
  - Write back to file

### 7. Briefing (`/api/briefing`)
- **GET /api/briefing**
  - Read `Dashboard.md` for stats
  - Count files in Done/, Pending_Approval/, etc.
  - Calculate metrics (tasks completed, time saved)
  - Read recent activity from logs

### 8. Accounting (`/api/odoo/`)
- **GET /api/odoo/summary**
  - Connect to Odoo via XML-RPC (if configured)
  - OR read from `AI_Employee_Vault/Accounting/` markdown files
  - Return revenue, expenses, invoices

## Implementation Steps

1. ✅ Create this plan document
2. ✅ Fix `/api/fte/status` route (typo correction)
3. ✅ Create `/api/fte/start` and `/api/fte/stop`
4. ✅ Implement real `/api/approvals` with file operations
5. ✅ Implement `/api/social/*` with vault integration
6. ✅ Implement `/api/email/*` with vault reading
7. ✅ Fix `/api/logs` to read real log files
8. ✅ Fix `/api/settings` to read/write actual .env
9. ✅ Create `/api/briefing` with vault stats aggregation
10. ✅ Implement `/api/odoo/sync` and `/api/fte/engine` (New)
11. ✅ Update frontend components to handle real data properly

## File Paths (Windows-compatible)
```typescript
const PROJECT_ROOT = process.env.PROJECT_ROOT || "C:\\Users\\kk\\Desktop\\Daniel's FTE";
const VAULT_PATH = path.join(PROJECT_ROOT, "AI_Employee_Vault");
const PYTHON_PATH = "python"; // or "python3"
```

## Security Considerations
- Check authentication before file operations
- Validate file paths to prevent directory traversal
- Use proper file locks for concurrent access
- Log all file movements for audit trail

## Testing Checklist
- [x] Start FTE from dashboard
- [x] Stop FTE from dashboard
- [x] Approve a pending item
- [x] Reject a pending item
- [x] Create a social post
- [x] View real logs
- [x] Toggle settings
- [x] View briefing stats
- [x] Switch to Qwen Autonomous Mode
- [x] Sync Odoo Transactions
