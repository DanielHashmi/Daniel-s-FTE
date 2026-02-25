#!/usr/bin/env bash

# Health monitor for Platinum Odoo cloud stack.
# Exits non-zero when:
# - HTTPS endpoint is unreachable
# - latest backup is older than configured max age

set -euo pipefail

URL="${ODOO_HEALTHCHECK_URL:-https://${ODOO_DOMAIN}/web/login}"
MAX_BACKUP_AGE_SECONDS="${MAX_BACKUP_AGE_SECONDS:-172800}"
BACKUP_DIR="${ODOO_BACKUP_DIR:-}"

if ! curl -fsS --max-time 20 "$URL" >/dev/null; then
  echo "ERROR: Odoo HTTPS healthcheck failed: $URL"
  exit 2
fi

if [ -n "$BACKUP_DIR" ] && [ -d "$BACKUP_DIR" ]; then
  latest_file="$(find "$BACKUP_DIR" -type f | sort | tail -n 1 || true)"
  if [ -z "$latest_file" ]; then
    echo "ERROR: No backups found in $BACKUP_DIR"
    exit 3
  fi
  now_epoch="$(date +%s)"
  file_epoch="$(stat -c %Y "$latest_file" 2>/dev/null || stat -f %m "$latest_file")"
  age="$((now_epoch - file_epoch))"
  if [ "$age" -gt "$MAX_BACKUP_AGE_SECONDS" ]; then
    echo "ERROR: Latest backup is stale (${age}s): $latest_file"
    exit 4
  fi
fi

echo "OK: Cloud Odoo healthcheck passed."
