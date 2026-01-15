# Silver Tier Quickstart

## Prerequisites
- Python 3.13+
- Node.js v24+
- PM2 (`npm install -g pm2`)
- Credentials for Gmail and LinkedIn

## 1. Setup Environment
```bash
cp .env.example .env
# Edit .env and add:
# GMAIL_CREDENTIALS_JSON=...
# LINKEDIN_ACCESS_TOKEN=...
```

## 2. Initialize Vault
Ensure your vault structure is ready:
```bash
/setup-vault
```

## 3. Verify Skills
Check that all automation skills are present:
```bash
ls .claude/skills/
# Should see: manage-approval, email-ops, social-ops, scheduler
```

## 4. Start Watchers (Dry Run)
Start the system in dry-run mode to verify connectivity without taking actions.
```bash
export DRY_RUN=true
python3 src/orchestrator.py
```

## 5. Test Workflow
1. Drop a file in `Inbox/` or simulate an email.
2. Observe `Needs_Action/` file creation.
3. Watch Claude generate a `Plan.md`.
4. Approve any pending actions in `Pending_Approval/`.
5. Verify success in `Logs/`.
