---
name: process-inbox
description: "WHAT: Process pending action files in Needs_Action folder, create execution plans, update Dashboard. WHEN: User says 'process inbox', 'handle pending actions', 'create plans for tasks'. Trigger on: inbox processing, action file handling, plan generation."
---

# Process Inbox

## When to Use
- After watcher has created action files in Needs_Action
- User wants to process pending tasks and create plans
- Scheduled processing runs (hourly/daily)
- Manual processing of specific priority items

## Instructions
1. Execute processing: `python3 scripts/main_operation.py [--vault-path AI_Employee_Vault] [--priority high|medium|low|all] [--max-files N]`
2. Verify results: `python3 scripts/verify_operation.py --vault-path AI_Employee_Vault`
3. Review generated plans in Plans/ folder.

## Validation
- [ ] Action files processed and moved to Done/
- [ ] Plan files created in Plans/
- [ ] Dashboard.md updated with activity
- [ ] No errors in processing

See [REFERENCE.md](./REFERENCE.md) for Company_Handbook rules and plan templates.
