# Platinum Tier Research Notes (Current Implementation)

## Local-First Control Plane (Synced Across Cloud + Local)

Decision: use `AI_Employee_Vault/` as the single source of truth for state.

Rationale:
- Auditable: approvals and outcomes are files
- Simple HITL: "approve by move" works without external services
- Works offline and across tools (UI, scripts, Obsidian)

## Cloud/Local Work-Zone Specialization

Decision: enforce role ownership with `AGENT_ROLE` and `STRICT_WORK_ZONES=true`.

Rationale:
- Prevents local agent from claiming cloud-owned drafting tasks
- Prevents cloud agent from drifting into local-only sensitive execution paths
- Keeps Platinum handover deterministic for demo and production-ish flows

## Qwen Invocation Strategy

Decision: invoke Qwen CLI with prompt passed via stdin using:

```
qwen -y --input-format text
```

Rationale:
- Avoids Windows quoting/escaping issues with `-p`
- Easier to normalize output and enforce "plain text only" constraints

## Facebook Automation Strategy

Decision: use Playwright Chromium **persistent context** with `user_data_dir=FACEBOOK_SESSION_DIR`.

Rationale:
- Session is captured once via an operator login step
- Subsequent post attempts reuse the same local browser profile directory
- Enables deterministic "open composer, fill textbox, click Post" automation

Operational safety:
- `DRY_RUN=true` prevents live posting
- Login/setup should be non-headless for transparency

## Orchestrator Liveness

Decision: write a heartbeat file (`AI_Employee_Vault/Logs/orchestrator_heartbeat.json`) on a short interval.

Rationale:
- Dashboard can display a reliable "brain running" indicator without needing sockets/services
- Avoids false negatives during long cycles by using a dedicated heartbeat loop
