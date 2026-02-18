# Cloud Deployment (Platinum)

This folder contains the production-ish cloud artifacts required by Hackathon 0 Platinum:

- 24/7 cloud orchestrator process (`AGENT_ROLE=cloud`) via PM2
- Odoo Community stack via Docker Compose
- HTTPS termination via Caddy
- automated DB backups
- health monitoring hooks

## Prerequisites

- Linux VM with Docker + Docker Compose plugin
- Node.js 20+ and PM2
- Python 3.12+ on the VM
- DNS A record for `ODOO_DOMAIN` pointing to the VM

## 1. Configure Environment

```bash
cp .env.cloud.example .env.cloud
```

Edit `.env.cloud` with real values:
- `ODOO_DOMAIN`
- `ACME_EMAIL`
- `ODOO_POSTGRES_PASSWORD`
- any optional overrides

## 2. Start Odoo + HTTPS + Backup

```bash
docker compose --env-file .env.cloud -f deployment/cloud/docker-compose.odoo.yml up -d
```

Services:
- `odoo` (app)
- `db` (postgres)
- `db-backup` (daily backups by default)
- `caddy` (automatic HTTPS certificates)

## 3. Start Cloud Orchestrator + Odoo MCP

```bash
pm2 start deployment/cloud/ecosystem.config.js
pm2 save
pm2 startup
```

The cloud orchestrator runs in draft-only mode by default (`DEV_MODE=true`) and writes approval files into `Pending_Approval/<domain>/`.

## 4. Health Monitoring

Manual check:

```bash
bash deployment/cloud/healthcheck_odoo.sh
```

Recommended cron (every 5 minutes):

```bash
*/5 * * * * ODOO_DOMAIN=odoo.example.com bash /path/to/repo/deployment/cloud/healthcheck_odoo.sh >> /var/log/odoo-health.log 2>&1
```

Optional backup age checks:

```bash
ODOO_BACKUP_DIR=/var/lib/docker/volumes/danielsfte_db-backups/_data \
MAX_BACKUP_AGE_SECONDS=172800 \
bash deployment/cloud/healthcheck_odoo.sh
```
