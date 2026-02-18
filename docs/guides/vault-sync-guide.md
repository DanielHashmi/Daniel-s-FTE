# Vault Sync Guide (Platinum Phase 1)

Platinum phase-1 coordination uses synced vault files instead of direct A2A messaging.

## Supported Sync Methods

## 1. Git-Based Sync (Recommended for auditability)

Pattern:
1. Cloud pulls latest
2. Cloud writes `Needs_Action/`, `Plans/`, `Pending_Approval/`, `Signals/`
3. Cloud commits + pushes
4. Local pulls and merges
5. Local executes approvals and updates `Dashboard.md`

Rules:
- Do not force-push sync branches.
- Keep commit frequency small and frequent.
- Avoid syncing transient runtime artifacts.

## 2. Syncthing-Based Sync

- Use `deployment/local/syncthing-config.toml` as baseline.
- Sync only vault state folders, not credentials/session directories.

## Security Rules

Never sync secrets:
- `.env*`
- token files
- social/whatsapp session folders
- banking credentials

Reference:
- `.gitignore`
- `.gitignore-sync`

## Conflict Policy

- Claim-by-move lock is authoritative:
  - First move to `In_Progress/<agent>/` owns task.
- Local agent is single writer for `Dashboard.md`.
- Cloud writes status updates to `Signals/`; Local merges into dashboard.
