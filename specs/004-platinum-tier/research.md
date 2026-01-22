# Platinum Tier Research Summary

## Vault Sync Mechanism
**Decision**: Syncthing (primary), Git fallback
**Rationale**: Syncthing provides real-time bidirectional sync (<10s latency), handles conflicts better for Markdown files, no merge conflicts like Git. Free, local-first. Git for backup/versioning.
**Alternatives**: Git (merge hell for concurrent writes), rsync (unidirectional), Dropbox (cloud dependency violates local-first)

## Odoo MCP Integration
**Decision**: Custom Python MCP server using xmlrpc.client (Odoo 19 compatible)
**Rationale**: Matches existing skill pattern, no extra deps, supports draft/live modes via env flags. JSON-RPC stable in 19, migrate to JSON-2 post-20.
**Alternatives**: odoo-xmlrpc lib (adds dep), direct API calls (violates MCP principle)

## Process Management
**Decision**: PM2 for all services (orchestrator, watchers, MCP)
**Rationale**: Cross-platform (Linux/Mac/Win), Python support, auto-restart, health checks, ecosystem file. Proven in Gold Tier.
**Alternatives**: systemd (Linux-only), supervisord (Python-only, more config)

## Cloud Provider
**Decision**: Oracle Cloud Free Tier (2 VMs)
**Rationale**: Always-free ARM instances (4 OCPU, 24GB RAM), sufficient for Odoo+PM2, no credit card for basic tier.
**Alternatives**: AWS Lightsail (paid), GCP f1-micro (limited CPU)

All clarifications resolved. Ready for design.