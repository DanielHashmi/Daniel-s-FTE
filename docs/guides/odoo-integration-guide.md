# Odoo Integration Guide (Optional)

This repo includes an optional Odoo accounting workflow:
- Run Odoo locally via Docker
- Sync posted transactions into `AI_Employee_Vault/Accounting/`
- Require approval before posting invoices (HITL)

## Prerequisites

- Docker Desktop installed and running
- Access Odoo on `http://localhost:8069`

## Start Odoo Locally

The simplest path on Windows is:

```powershell
START_ODOO.bat
```

This uses `docker-compose-odoo.yml` (Odoo 16 + Postgres). After it starts:

1. Open `http://localhost:8069`
2. Create a database (recommended test values):
   - Database Name: `odoo`
   - Email: `admin`
   - Password: `admin`
   - Enable "Demo data" for testing
3. Install the "Invoicing" (or Accounting) app

Note: There is also `deployment/cloud/docker-compose.odoo.yml` (newer Odoo + backup container) if you want that layout instead.

## Configure `.env`

Set these env vars in the repo root `.env` (gitignored):

```bash
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=admin
ODOO_PASSWORD=admin

# Optional safety switch
DRY_RUN=true
```

The Odoo client uses Odoo JSON-RPC (`/jsonrpc`) for Odoo 19+ compatibility.

## Test The Odoo Skill (CLI)

The integration is implemented in:
- `.claude/skills/odoo-accounting/scripts/main_operation.py`

Examples:

```bash
# Sync posted transactions into the vault (default mode: draft)
python .claude/skills/odoo-accounting/scripts/main_operation.py sync

# Generate a summary
python .claude/skills/odoo-accounting/scripts/main_operation.py --mode draft summary

# Create a draft invoice report (CSV)
python .claude/skills/odoo-accounting/scripts/main_operation.py --mode draft draft-report
```

Synced transactions are written to:
- `AI_Employee_Vault/Accounting/transactions/YYYY-MM/transactions.json`

## Approval Flow: Posting Invoices (Live Mode)

When you run a post in live mode with approvals enabled:

```bash
python .claude/skills/odoo-accounting/scripts/main_operation.py --mode live post 15
```

It creates:
- `AI_Employee_Vault/Pending_Approval/invoice_15_approval.yaml`

To execute it, move it to:
- `AI_Employee_Vault/Approved/`

If the orchestrator is running, it will detect the approved YAML and post the invoice (unless `DRY_RUN=true`).

## Troubleshooting

- Docker is running but Odoo is not reachable:
  - Confirm the containers are up (`docker ps`) and port `8069` is mapped.
- Authentication errors:
  - Verify `ODOO_DB`, `ODOO_USERNAME`, `ODOO_PASSWORD` match the database you created.
