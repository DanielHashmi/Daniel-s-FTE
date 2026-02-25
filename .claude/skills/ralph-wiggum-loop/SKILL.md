---
name: ralph-wiggum-loop
description: "Execute persistent multi-step orchestration cycles until completion or iteration limit."
---

# Ralph Wiggum Loop

Use this skill when you need autonomous iteration over multi-step work with HITL-safe pause behavior.

## Command

```bash
python .claude/skills/ralph-wiggum-loop/scripts/main_operation.py \
  --prompt "Process all pending tasks to completion" \
  --max-iterations 10 \
  --sleep 2
```

Watch-file completion mode:

```bash
python .claude/skills/ralph-wiggum-loop/scripts/main_operation.py \
  --prompt "Process invoice workflow end-to-end" \
  --watch-file "Needs_Action/INVOICE_act_1234.md" \
  --max-iterations 12 \
  --sleep 2
```

## Behavior

- Creates active state under `AI_Employee_Vault/Ralph_State/`
- Runs one orchestrator cycle per iteration
- Pauses if `Pending_Approval/` contains items (HITL)
- Completes when:
  - watched file leaves active location (watch-file mode), or
  - workflow queues are empty (queue mode)
- Archives final state to `AI_Employee_Vault/Ralph_History/`

## Validation

- [ ] State file created during run
- [ ] Iteration count increments
- [ ] HITL pause occurs when approvals exist
- [ ] Completed or max-iteration terminal status is written
