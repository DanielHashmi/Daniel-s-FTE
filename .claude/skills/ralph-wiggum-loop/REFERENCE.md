# Ralph Wiggum Loop Reference

## Stop Hook Implementation

The Ralph Wiggum loop uses Claude Code's stop hook mechanism to persist task execution. The stop hook intercepts Claude's exit attempt and decides whether to allow it or re-inject the prompt.

### Hook Configuration

Add to `.claude/hooks/stop.js`:
```javascript
module.exports = async function stopHook(context) {
  const fs = require('fs');
  const path = require('path');

  const stateDir = path.join(process.cwd(), 'AI_Employee_Vault', 'Ralph_State');

  // Find active loop state
  const stateFiles = fs.readdirSync(stateDir)
    .filter(f => f.startsWith('RALPH_') && f.endsWith('.json'));

  if (stateFiles.length === 0) {
    return { allowExit: true };
  }

  const state = JSON.parse(fs.readFileSync(path.join(stateDir, stateFiles[0])));

  // Check completion conditions
  if (state.completion_promise) {
    // Check if output contains promise
    if (context.output.includes(`<promise>${state.completion_promise}</promise>`)) {
      return { allowExit: true, reason: 'Completion promise detected' };
    }
  }

  if (state.watch_file) {
    // Check if file moved to Done
    const doneFile = path.join(state.done_folder, path.basename(state.watch_file));
    if (fs.existsSync(doneFile)) {
      return { allowExit: true, reason: 'Task file moved to Done' };
    }
  }

  // Check iteration limit
  if (state.current_iteration >= state.max_iterations) {
    return { allowExit: true, reason: 'Max iterations reached' };
  }

  // Continue loop
  return {
    allowExit: false,
    injectPrompt: state.prompt,
    message: `Continuing loop (iteration ${state.current_iteration + 1}/${state.max_iterations})`
  };
};
```

## Completion Strategies

### Promise-Based
Claude outputs a specific string when done:
```
<promise>TASK_COMPLETE</promise>
```

Pros:
- Simple to implement
- Works for any task type
- Claude decides when complete

Cons:
- Relies on Claude's judgment
- May complete prematurely or never

### File-Movement Based
The loop monitors a specific file and completes when it's moved to Done/:
```bash
--watch-file "Needs_Action/INVOICE_client.md" --done-folder "Done/"
```

Pros:
- More reliable (objective completion)
- Natural part of existing workflow
- No special output required

Cons:
- Requires file-based task tracking
- Task must involve file movement

## State Management

### State File Structure
```json
{
  "loop_id": "RALPH_20260119_abc123",
  "prompt": "Process all invoices...",
  "max_iterations": 10,
  "completion_promise": "TASK_COMPLETE",
  "current_iteration": 3,
  "status": "running",
  "started_at": "2026-01-19T10:00:00Z",
  "iterations": [
    {
      "number": 1,
      "timestamp": "2026-01-19T10:00:05Z",
      "output_preview": "Processing invoice 1...",
      "completed": false
    }
  ],
  "errors": [],
  "paused_for_approval": false
}
```

### Status Values
- `pending` - Created but not started
- `running` - Actively executing
- `paused_awaiting_approval` - Waiting for HITL approval
- `completed` - Successfully finished
- `max_iterations_reached` - Hit limit without completion
- `stopped` - Manually stopped

## HITL Integration

When a loop encounters a sensitive action requiring approval:
1. Loop pauses and sets `paused_for_approval: true`
2. Creates approval request in `/Pending_Approval/`
3. Waits for file to appear in `/Approved/`
4. Automatically resumes after approval

## Error Handling

### Transient Errors
- Automatic retry with exponential backoff
- Logged in `errors` array
- Continues after recovery

### Fatal Errors
- Loop stops immediately
- Creates human review request
- Logs full error details

## Performance Tuning

| Parameter | Default | Recommended Range |
|-----------|---------|-------------------|
| max_iterations | 10 | 5-20 |
| timeout | 3600s | 1800-7200s |
| pause between iterations | 1s | 1-5s |

## Troubleshooting

### Loop never completes
- Check completion promise spelling
- Verify watch file path
- Increase max_iterations

### Loop completes too early
- Use more specific completion promise
- Switch to file-movement strategy

### Memory issues
- Reduce max_iterations
- Clear Ralph_History periodically
