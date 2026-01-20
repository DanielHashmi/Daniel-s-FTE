# Platinum Tier Quickstart

## 1. Cloud VM Setup (Oracle Free Tier)
1. Create ARM Ampere A1 instance (4 OCPU, 24GB)
2. Install Ubuntu 22.04
3. SSH key auth only

## 2. Odoo Deployment
```
curl -fsSL https://get.docker.com -o get-docker.com.sh
sh get-docker.com.sh
docker run -d -p 8069:8069 --name odoo -v odoo-data:/var/lib/odoo -e POSTGRES_PASSWORD=odoo odoo:19.0
```

## 3. Clone Repo & PM2
```
git clone https://github.com/DanielHashmi/Daniel-s-FTE.git ai-employee
cd ai-employee
npm i -g pm2
pm2 start ecosystem.config.js
pm2 save
```

## 4. Local Setup
```
git clone https://github.com/DanielHashmi/Daniel-s-FTE.git ai-employee-local
cd ai-employee-local
# Install Syncthing, point to shared vault dir
syncthing --generate="~/.config/syncthing"
```

## 5. Vault Sync
- Syncthing folders: `/path/to/AI_Employee_Vault` (bidirectional)
- Exclude: `.git`, `node_modules`, `.env`

## 6. Test Handover
1. Kill local agent
2. Send test email
3. Verify cloud draft in /Pending_Approval
4. Restart local, approve, verify execution