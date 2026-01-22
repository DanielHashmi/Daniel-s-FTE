# Step-by-Step Odoo Integration Guide

This guide will help you integrate Odoo 19 (Community Edition) with your AI Employee, completing the Platinum Tier financial workflow.

## Current Status
- **Codebase**: Fully prepared. Odoo MCP server and Agent Skills are implemented.
- **Configuration**: Added default credentials to your `.env` file.
- **Environment**: Docker is required but currently not detected in your WSL environment.

---

## Step 1: Enable Docker (Prerequisite)
Your system needs Docker to run the Odoo database and application containers.

1.  **Install Docker Desktop** on Windows.
2.  Go to **Settings > Resources > WSL Integration**.
3.  Enable integration for your specific Linux distro (e.g., `Ubuntu`).
4.  Restart your terminal.
5.  Verify by running: `docker ps`

## Step 2: Deploy Odoo
Once Docker is ready, deploy the pre-configured Odoo stack.

1.  Navigate to the cloud deployment folder:
    ```bash
    cd deployment/cloud
    ```
2.  Start the services:
    ```bash
    docker-compose -f docker-compose.odoo.yml up -d
    ```
3.  Wait for initialization (approx. 1-2 minutes). Access Odoo at `http://localhost:8069`.
    *   **Email**: `odoo`
    *   **Password**: `odoo_password`

## Step 3: Configure Credentials
I have already added default credentials to your `.env` file. If you changed them during setup, update them now:

```bash
# Edit .env file
nano .env

# Verify/Update these values:
ODOO_URL=http://localhost:8069
ODOO_DB=odoo
ODOO_USERNAME=odoo
ODOO_PASSWORD=odoo_password  # Or API Key if using 2FA
```

## Step 4: Verify Connection
Use the built-in skill script to test the connection.

1.  **Test Connection & Generate Report** (Draft Mode):
    ```bash
    python3 .claude/skills/odoo-accounting/scripts/main_operation.py --mode draft summary
    ```
    *Success*: You should see a JSON output with "total_draft" count.
    *Failure*: Check if Docker is running and credentials match.

## Step 5: Start the Odoo MCP Server
The Odoo MCP server (`odoo-mcp.js`) allows the AI to interact with Odoo autonomously.

1.  **Start via PM2**:
    ```bash
    pm2 start ecosystem.config.js --only odoo-mcp
    ```
2.  **Verify Status**:
    ```bash
    pm2 status
    pm2 logs odoo-mcp
    ```

## Step 6: Test the Autonomous Workflow
Test the full loop from "Draft" to "Posted".

1.  **Create a Draft Invoice** manually in Odoo (`http://localhost:8069`) for testing.
2.  **Ask the AI to sync**: "Sync Odoo invoices."
3.  **Approve the Post**:
    *   The AI will create an approval request in `AI_Employee_Vault/Pending_Approval/`.
    *   Move the file to `Approved/` to authorize posting.
    *   The AI will post it to Odoo (Live Mode).

## Troubleshooting
-   **"Docker not found"**: Ensure WSL integration is enabled in Docker Desktop.
-   **"Connection Refused"**: Ensure Odoo container is running (`docker ps`) and port 8069 is exposed.
-   **"Authentication Failed"**: Verify `ODOO_PASSWORD` in `.env`.
