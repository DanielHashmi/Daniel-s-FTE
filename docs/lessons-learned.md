# Lessons Learned

This summarizes engineering lessons from implementing Bronze -> Platinum tiers.

## 1. File-Based HITL Is Robust

- A simple folder state machine (`Pending_Approval`, `Approved`, `Rejected`, `Done`) is auditable and understandable.
- It reduces accidental side effects compared to direct autonomous API actions.

## 2. Role Separation Prevents Risk Creep

- Explicit cloud/local ownership (`AGENT_ROLE`, `STRICT_WORK_ZONES`) prevents mixed responsibility.
- Cloud draft-only mode significantly reduces blast radius for always-on automation.

## 3. Claim-By-Move Works Well for Multi-Agent Coordination

- Moving files into `In_Progress/<agent>` is an effective lock primitive on a shared vault.
- It avoids duplicate execution without central coordination infrastructure.

## 4. MCP as the Action Boundary Scales

- Centralizing external actions through MCP servers simplifies policy enforcement.
- `DRY_RUN` and rate limiting are easier to apply consistently at this boundary.

## 5. Browser Automation Requires Operational UX

- Social/web actions (Facebook/LinkedIn/WhatsApp) need session-capture workflow and clear operator tooling.
- Headless-only assumptions are fragile during setup and auth refresh.

## 6. Observability Is Mandatory

- Heartbeats, structured logs, and daily summaries are required for trust in unattended runs.
- Without clear logs, debugging multi-step failures is expensive.

## 7. Cloud Deployment Needs Production Controls Early

- HTTPS, backups, health checks, and PM2 restarts are not optional at Platinum.
- Deferring them causes reliability regressions late in integration.

## 8. Test Drift Is Real

- As architecture evolves, integration tests can silently become legacy.
- Keeping tests aligned with current contracts is as important as adding new tests.

## Next Iteration Recommendations

1. Add explicit dashboard session-capture actions for social channels.
2. Add stricter dashboard auth/CSRF/session controls.
3. Add continuous compliance checks that validate tier requirements from source checklist.
