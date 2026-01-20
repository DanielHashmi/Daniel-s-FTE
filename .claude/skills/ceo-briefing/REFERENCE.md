# CEO Briefing Reference

## Scheduling

### Linux/Mac (cron)
```cron
# Every Monday at 7:00 AM
0 7 * * 1 cd /path/to/project && python3 .claude/skills/ceo-briefing/scripts/main_operation.py --action generate
```

### Windows (Task Scheduler)
1. Open Task Scheduler
2. Create Basic Task → "CEO Briefing"
3. Trigger: Weekly, Monday 7:00 AM
4. Action: Start a program
   - Program: `python3`
   - Arguments: `.claude/skills/ceo-briefing/scripts/main_operation.py --action generate`
   - Start in: `/path/to/project`

## Data Sources

### Financial Data
Primary: `AI_Employee_Vault/Accounting/transactions_*.json`
- Synced from Odoo accounting skill
- Falls back to sample data if unavailable

### Task Data
Primary: `AI_Employee_Vault/Done/`
- Analyzes file modification dates
- Extracts task names from filenames

### Goals & Deadlines
Primary: `AI_Employee_Vault/Business_Goals.md`
- Parses dates in YYYY-MM-DD format
- Extracts deadlines from bullet points

## Customization

### Briefing Sections
Edit `main_operation.py` to add/remove sections:
- Executive Summary (always included)
- Revenue (requires accounting data)
- Completed Tasks
- Bottlenecks (requires historical data)
- Cost Optimization
- Upcoming Deadlines
- Proactive Suggestions

### Thresholds
```python
# Revenue trend thresholds
AHEAD_THRESHOLD = 60  # % of monthly goal
ON_TRACK_THRESHOLD = 45

# Deadline risk threshold
AT_RISK_DAYS = 7  # Flag if deadline within N days

# Subscription review threshold
UNUSED_DAYS = 30  # Flag if no activity in N days
```

## Output Format

Briefings are Markdown files compatible with:
- Obsidian
- GitHub/GitLab
- Any Markdown viewer

File naming: `YYYY-MM-DD_Monday_Briefing.md`

## Troubleshooting

### "No financial data"
Run Xero sync first: `python3 .claude/skills/odoo-accounting/scripts/main_operation.py --action sync`

### "No tasks found"
Ensure completed tasks are moved to `/Done` folder.

### "Missing deadlines"
Update `Business_Goals.md` with dates in YYYY-MM-DD format.
