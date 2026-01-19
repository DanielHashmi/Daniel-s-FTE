---
name: cross-domain-orchestrator
description: "WHAT: Coordinate operations across Personal and Business domains, manage workflow dependencies, and orchestrate multi-system tasks. WHEN: User says 'coordinate workflow', 'cross-domain task', 'orchestrate systems'. Trigger on: multi-domain operations, complex workflows, system coordination."
---

# Cross-Domain Orchestrator

## When to Use
- Coordinating tasks spanning Personal and Business domains
- Managing dependencies between different systems
- Orchestrating complex multi-step workflows
- Running scheduled coordination (daily sync, weekly audit)
- Handling cross-system data flow

## Domains Managed

### Personal Domain
- Gmail (email communications)
- WhatsApp (messaging)
- Personal calendar
- Personal files

### Business Domain
- Xero (accounting)
- LinkedIn (professional networking)
- Facebook/Instagram/Twitter (social media)
- Business calendar
- Project files

## Instructions

1. **Full System Sync**:
   ```bash
   python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action sync-all
   ```
   *Syncs: Gmail, WhatsApp, LinkedIn, Xero, Social media status*

2. **Domain-Specific Sync**:
   ```bash
   python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action sync --domain personal
   python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action sync --domain business
   ```

3. **Run Scheduled Coordination**:
   ```bash
   python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action run-schedule --schedule daily
   ```
   *Options: `--schedule daily|weekly|monthly`*

4. **Check System Health**:
   ```bash
   python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action health
   ```
   *Reports status of all integrated systems.*

5. **Process Cross-Domain Workflow**:
   ```bash
   python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action workflow \
     --workflow "client-invoice-flow" \
     --params '{"client": "Acme Corp", "amount": 1500}'
   ```

6. **View Integration Map**:
   ```bash
   python3 .claude/skills/cross-domain-orchestrator/scripts/main_operation.py --action map
   ```

## Pre-Built Workflows

### client-invoice-flow
1. Check Xero for services rendered
2. Generate invoice PDF
3. Send via Gmail
4. Post LinkedIn update (optional)
5. Log transaction

### weekly-business-audit
1. Sync all Xero data
2. Analyze transactions
3. Check task completion
4. Generate CEO Briefing
5. Send email summary

### social-media-campaign
1. Generate content
2. Create approval requests (all platforms)
3. Post to approved platforms
4. Track engagement
5. Report results

## Configuration
`AI_Employee_Vault/Config/orchestrator_config.yaml`:
```yaml
domains:
  personal:
    gmail: enabled
    whatsapp: enabled
  business:
    xero: enabled
    linkedin: enabled
    social: enabled

schedules:
  daily_sync: "06:00"
  weekly_audit: "monday 07:00"
  social_posting: "09:00,15:00"
```

## Validation
- [ ] All systems reachable
- [ ] Workflows execute in order
- [ ] Cross-domain data flows correctly
- [ ] Errors handled gracefully
- [ ] Audit log entries created

See [REFERENCE.md](./REFERENCE.md) for workflow definitions.
