# Quick Reference: Real Dashboard Features

## 🚀 Quick Start Testing

```powershell
# 1. Test all APIs
cd dashboard
.\test-apis.ps1

# 2. Open dashboard
http://localhost:3000/dashboard

# 3. Test approval workflow
# Create post → Go to approvals → Click approve → Check vault folder
```

## 📁 Real File Locations

| What | Where |
|------|-------|
| FTE Status | `AI_Employee_Vault\.fte_status` |
| Pending Items | `AI_Employee_Vault\Pending_Approval\*.md` |
| Approved Items | `AI_Employee_Vault\Approved\*.md` |
| Completed | `AI_Employee_Vault\Done\*.md` |
| Logs | `AI_Employee_Vault\Logs\*.log` |
| Signals | `AI_Employee_Vault\Signals\*.signal` |
| Config | `.env` |

## 🔧 Real API Endpoints

| Method | Endpoint | Does |
|--------|----------|------|
| GET | `/api/fte/status` | Check if FTE running |
| POST | `/api/fte/start` | Launch orchestrator |
| POST | `/api/fte/stop` | Kill processes |
| GET | `/api/approvals` | List pending items |
| POST | `/api/approvals/[id]` | Approve/reject |
| POST | `/api/social/post` | Create post |
| GET | `/api/social/posts` | List posts |
| GET | `/api/email/inbox` | Get emails |
| GET | `/api/logs` | Fetch logs |
| GET | `/api/settings` | Read .env |
| PATCH | `/api/settings` | Update .env |
| GET | `/api/briefing` | Get stats |
| GET | `/api/odoo/summary` | Accounting data |

## 🧪 Manual Testing Commands

```powershell
# Check if FTE is running
cat AI_Employee_Vault\.fte_status

# See pending approvals
dir AI_Employee_Vault\Pending_Approval\*.md

# Check approved items
dir AI_Employee_Vault\Approved\*.md

# View completed tasks
dir AI_Employee_Vault\Done\*.md

# Check signals
dir AI_Employee_Vault\Signals\*.signal

# View current settings
cat .env | Select-String "DRY_RUN","REQUIRE"

# Check for Python processes
tasklist | findstr python.exe

# View latest logs
cat AI_Employee_Vault\Logs\*.log | Select-Object -Last 20
```

## 📝 Create Test Data

```powershell
# Create test email
$email = @"
---
type: email
from: test@example.com
subject: Test Email
received: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
priority: normal
---

This is a test email for the AI Employee.
"@

$email | Out-File "AI_Employee_Vault\Needs_Action\EMAIL_test_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

# Create test social post approval
$post = @"
---
type: social
action: post
platform: twitter
status: pending
created: $(Get-Date -Format "yyyy-MM-ddTHH:mm:ssZ")
priority: normal
---

## Content
This is a test social media post!

*This post requires approval before posting*
"@

$post | Out-File "AI_Employee_Vault\Pending_Approval\SOCIAL_POST_$(Get-Date -Format 'yyyyMMdd_HHmmss').md"

# Create completed tasks for stats
echo "Task 1" > "AI_Employee_Vault\Done\EMAIL_completed1.md"
echo "Task 2" > "AI_Employee_Vault\Done\EMAIL_completed2.md"
echo "Task 3" > "AI_Employee_Vault\Done\SOCIAL_completed1.md"

Write-Host "✅ Test data created!" -ForegroundColor Green
```

## 🎯 Expected Behavior

### When You Click "Start FTE":
1. `POST /api/fte/start` is called
2. Launches `python orchestrator.py`
3. Starts watcher scripts
4. Writes `running` to `.fte_status`
5. Process appears in Task Manager

### When You Click "Approve":
1. `POST /api/approvals/[id]` with `action: approve`
2. File moves from `Pending_Approval/` to `Approved/`
3. Signal file created in `Signals/`
4. Approval disappears from pending list

### When You Create a Post:
1. `POST /api/social/post` with content
2. New `.md` file created in `Pending_Approval/`
3. File has frontmatter with metadata
4. Appears in approvals list

### When You Toggle Settings:
1. `PATCH /api/settings` with toggle value
2. `.env` file is updated
3. Value persists on page reload

## 🔍 Debugging

### If FTE won't start:
```powershell
# Check Python is installed
python --version

# Try starting manually
python src/orchestration/orchestrator.py

# Check for errors
cat orchestrator.log
```

### If approvals don't show:
```powershell
# Check folder exists
Test-Path AI_Employee_Vault\Pending_Approval

# List files
dir AI_Employee_Vault\Pending_Approval\*.md

# Check file format
cat "AI_Employee_Vault\Pending_Approval\SOCIAL_*.md" | Select-Object -First 20
```

### If API calls fail:
```powershell
# Test endpoint directly
curl http://localhost:3000/api/approvals

# Check dashboard is running
Get-Process | Where-Object {$_.ProcessName -like "*node*"}

# View terminal output
# (Check the terminal running START_DASHBOARD.bat)
```

## 📊 Stats Calculation

| Metric | How It's Calculated |
|--------|---------------------|
| Tasks Completed | Count of .md files in `Done/` |
| Emails Processed | Count of EMAIL_*.md in `Done/` |
| Social Posts | Count of SOCIAL_*.md in `Done/` |
| Pending Approvals | Count of .md files in `Pending_Approval/` |
| Time Saved | Tasks × 5 minutes |

## 🎨 UI Pages

| URL | Real Data Source |
|-----|------------------|
| `/dashboard` | Vault folders + .fte_status |
| `/dashboard/fte` | Process list + logs |
| `/dashboard/approvals` | Pending_Approval folder |
| `/dashboard/social` | Multiple vault folders |
| `/dashboard/email` | Needs_Action folder |
| `/dashboard/logs` | Logs folder |
| `/dashboard/settings` | .env file |
| `/dashboard/briefing` | Aggregated vault stats |
| `/dashboard/accounting` | Accounting folder |

## ✅ Verification Checklist

- [ ] APIs respond (run test-apis.ps1)
- [ ] FTE can start/stop
- [ ] Processes appear in Task Manager
- [ ] .fte_status updates
- [ ] Approvals list shows real files
- [ ] Approve moves file to Approved/
- [ ] Reject moves file to Rejected/
- [ ] Signal files are created
- [ ] Social post creates .md file
- [ ] Settings toggle updates .env
- [ ] Briefing shows real counts
- [ ] Logs display real entries

## 🚨 Important Notes

- **Windows only** - Uses tasklist/taskkill
- **No auth yet** - Anyone can access
- **Polling not real-time** - 5-10s delay
- **Basic error handling** - Check logs for issues

---

**The dashboard now controls your REAL AI Employee system!** 🎉
