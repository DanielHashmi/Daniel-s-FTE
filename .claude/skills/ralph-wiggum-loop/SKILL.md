---
name: ralph-wiggum-loop
description: "WHAT: Execute autonomous multi-step tasks until completion using persistent iteration loop. WHEN: User says 'run ralph loop', 'autonomous task', 'complete workflow', 'multi-step task'. Trigger on: complex workflows, batch processing, unattended execution, overnight tasks."
---

# Ralph Wiggum Loop - Autonomous Task Executor

## When to Use
- Executing multi-step tasks autonomously (5+ steps)
- Running unattended batch operations
- Processing task queues to completion
- Overnight workflow execution
- Any task requiring persistence until completion

## How It Works
1. Creates state file with task prompt
2. Claude works on the task
3. Claude attempts to exit
4. Stop hook checks: Is task complete (file in Done/ or promise output)?
5. **YES** → Allow exit (success)
6. **NO** → Block exit, re-inject prompt, continue
7. Repeat until complete or max iterations reached

## Instructions

1. **Start Ralph Loop** (promise-based completion):
   ```bash
   python3 .claude/skills/ralph-wiggum-loop/scripts/main_operation.py --action start \
     --prompt "Process all files in Needs_Action/, move to Done/ when complete" \
     --completion-promise "TASK_COMPLETE" \
     --max-iterations 10
   ```

2. **Start Ralph Loop** (file-movement completion):
   ```bash
   python3 .claude/skills/ralph-wiggum-loop/scripts/main_operation.py --action start \
     --prompt "Process invoice request and send email" \
     --watch-file "Needs_Action/INVOICE_client_a.md" \
     --done-folder "Done/" \
     --max-iterations 10
   ```

3. **Check Loop Status**:
   ```bash
   python3 .claude/skills/ralph-wiggum-loop/scripts/main_operation.py --action status
   ```

4. **Stop Active Loop**:
   ```bash
   python3 .claude/skills/ralph-wiggum-loop/scripts/main_operation.py --action stop --loop-id LOOP_ID
   ```

5. **View Loop History**:
   ```bash
   python3 .claude/skills/ralph-wiggum-loop/scripts/main_operation.py --action history --limit 10
   ```

## Completion Strategies

### Promise-Based (Simple)
Claude outputs `<promise>TASK_COMPLETE</promise>` when done.
- Faster setup
- Relies on Claude's judgment

### File-Movement (Robust)
Stop hook detects when task file moves to Done/.
- More reliable
- Natural part of existing workflow
- Recommended for production

## Configuration Options
| Option | Default | Description |
|--------|---------|-------------|
| `--max-iterations` | 10 | Maximum loop cycles |
| `--timeout` | 3600 | Max seconds per iteration |
| `--pause-on-approval` | true | Pause when HITL needed |
| `--auto-resume` | true | Resume after approval |
| `--log-iterations` | true | Log each iteration |

## State Files
- `AI_Employee_Vault/Ralph_State/` - Active loop state
- `AI_Employee_Vault/Ralph_History/` - Completed loop logs

## Safety Features
- Maximum iteration limit prevents infinite loops
- Timeout per iteration prevents hangs
- Automatic HITL pause for sensitive actions
- Detailed logging for debugging
- Human review request on max iterations

## Validation
- [ ] State file created
- [ ] Iterations logged
- [ ] Completion detected correctly
- [ ] HITL pause working
- [ ] Max iterations respected

See [REFERENCE.md](./REFERENCE.md) for stop hook implementation.
