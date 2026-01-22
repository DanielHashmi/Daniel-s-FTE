---
name: ceo-briefing
description: "WHAT: Generate weekly business audit and CEO briefing with revenue, tasks, bottlenecks, and proactive suggestions. WHEN: User says 'generate briefing', 'weekly report', 'business summary', 'monday briefing'. Trigger on: Monday 7AM (scheduled), business review, strategic planning."
---

# CEO Briefing Generator

## When to Use
- Generating Monday morning business briefings (automated weekly)
- On-demand business performance review
- Preparing for strategic planning meetings
- Analyzing operational bottlenecks
- Identifying cost optimization opportunities

## Instructions

1. **Generate Weekly Briefing**:
   ```bash
   python3 .claude/skills/ceo-briefing/scripts/main_operation.py --action generate
   ```
   *Analyzes past 7 days. Output: `Briefings/YYYY-MM-DD_Monday_Briefing.md`*

2. **Custom Period Briefing**:
   ```bash
   python3 .claude/skills/ceo-briefing/scripts/main_operation.py --action generate --start 2026-01-01 --end 2026-01-15
   ```

3. **Revenue Analysis Only**:
   ```bash
   python3 .claude/skills/ceo-briefing/scripts/main_operation.py --action revenue --period weekly
   ```

4. **Task Analysis** (bottleneck detection):
   ```bash
   python3 .claude/skills/ceo-briefing/scripts/main_operation.py --action tasks --detect-bottlenecks
   ```

5. **Subscription Audit**:
   ```bash
   python3 .claude/skills/ceo-briefing/scripts/main_operation.py --action subscriptions --unused-threshold 30
   ```
   *Flags subscriptions with no activity in N days.*

6. **Deadline Tracker**:
   ```bash
   python3 .claude/skills/ceo-briefing/scripts/main_operation.py --action deadlines --horizon 14
   ```
   *Lists deadlines from Business_Goals.md within N days.*

## Briefing Sections
1. **Executive Summary** - High-level overview
2. **Revenue** - Weekly total, MTD, goal progress, trend
3. **Completed Tasks** - With duration analysis
4. **Bottlenecks** - Tasks exceeding expected duration
5. **Cost Optimization** - Unused subscriptions, savings opportunities
6. **Upcoming Deadlines** - Next 14 days with risk assessment
7. **Proactive Suggestions** - AI-generated recommendations

## Data Sources
- `AI_Employee_Vault/Accounting/` - Financial data (Xero sync)
- `AI_Employee_Vault/Done/` - Completed task files
- `AI_Employee_Vault/Business_Goals.md` - Targets and deadlines
- `AI_Employee_Vault/Logs/` - Activity patterns

## Scheduling
Add to cron for automatic weekly generation:
```bash
0 7 * * 1 cd /path/to/project && python3 .claude/skills/ceo-briefing/scripts/main_operation.py --action generate
```

## Validation
- [ ] All data sources accessible
- [ ] Financial calculations accurate
- [ ] Briefing file created successfully
- [ ] All sections populated
- [ ] Audit log entry created

See [REFERENCE.md](./REFERENCE.md) for customization options.
