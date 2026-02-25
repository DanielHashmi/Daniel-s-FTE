#!/usr/bin/env bash

# Cloud bootstrap for Platinum tier:
# - validates Node/PM2
# - validates Docker + Docker Compose
# - prepares cloud env file
# - validates PM2 app config

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$ROOT_DIR"

echo "========================================="
echo "Cloud FTE Setup"
echo "========================================="

if ! command -v node >/dev/null 2>&1; then
  echo "ERROR: Node.js is required (20+)."
  exit 1
fi
NODE_MAJOR="$(node --version | sed 's/^v//' | cut -d'.' -f1)"
if [ "${NODE_MAJOR}" -lt 20 ]; then
  echo "ERROR: Node.js 20+ required. Found: $(node --version)"
  exit 1
fi
echo "Node.js OK: $(node --version)"

if ! command -v npm >/dev/null 2>&1; then
  echo "ERROR: npm is required."
  exit 1
fi

if ! command -v pm2 >/dev/null 2>&1; then
  echo "Installing PM2 globally..."
  npm install -g pm2
fi
echo "PM2 OK: $(pm2 --version)"

if ! command -v docker >/dev/null 2>&1; then
  echo "ERROR: Docker is required for Odoo deployment."
  exit 1
fi
if ! docker compose version >/dev/null 2>&1; then
  echo "ERROR: Docker Compose plugin is required."
  exit 1
fi
echo "Docker OK: $(docker --version)"

if [ ! -f ".env.cloud.example" ]; then
  echo "ERROR: .env.cloud.example missing."
  exit 1
fi
if [ ! -f ".env.cloud" ]; then
  cp ".env.cloud.example" ".env.cloud"
  echo "Created .env.cloud from .env.cloud.example"
else
  echo ".env.cloud already exists"
fi

echo
echo "Validating PM2 ecosystem..."
pm2 prettylist >/dev/null 2>&1 || true
node -e "require('./deployment/cloud/ecosystem.config.js'); console.log('PM2 config load: OK')"

echo
echo "========================================="
echo "Next steps"
echo "========================================="
echo "1) Edit .env.cloud with production credentials and domain."
echo "2) Start Odoo stack:"
echo "   docker compose --env-file .env.cloud -f deployment/cloud/docker-compose.odoo.yml up -d"
echo "3) Start cloud orchestrator + Odoo MCP:"
echo "   pm2 start deployment/cloud/ecosystem.config.js"
echo "4) Persist PM2 on reboot:"
echo "   pm2 save && pm2 startup"
echo
