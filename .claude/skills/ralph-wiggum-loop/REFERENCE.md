# Ralph Wiggum Loop Reference

The skill script is:

`python .claude/skills/ralph-wiggum-loop/scripts/main_operation.py`

## CLI Options

- `--prompt` (required): task objective recorded in loop state
- `--max-iterations` (default `10`): iteration cap
- `--watch-file`: optional vault-relative file path used as completion marker
- `--sleep` (default `2.0`): delay between iterations

## Completion Modes

1. Watch-file mode  
   Loop completes when watched file is moved/removed from active queues (typically into `Done/`).

2. Queue-empty mode  
   Loop completes when `Needs_Action`, `Pending_Approval`, `Approved`, and `In_Progress` are empty.

## HITL Pause

If `Pending_Approval/` contains items, the loop writes state `paused_awaiting_approval` and exits that run safely.

## State Files

- Active: `AI_Employee_Vault/Ralph_State/<loop_id>.json`
- Archived: `AI_Employee_Vault/Ralph_History/<loop_id>.json`

## Example

```bash
python .claude/skills/ralph-wiggum-loop/scripts/main_operation.py \
  --prompt "Complete all billing-related tasks" \
  --watch-file "Needs_Action/business/FINANCE_act_1a2b3c.md" \
  --max-iterations 15 \
  --sleep 2
```
