# AI Employee Platinum Tier - Demo Script

## Introduction (0:00-1:00)
- **Concept**: Presenting the Personal AI Employee (Digital FTE).
- **Vision**: "Your life and business on autopilot. Local-first, agent-driven, human-in-the-loop."
- **Dashboard**: Show Obsidian Dashboard.md with status "Platinum Tier - Sync Active".

## Scenario 1: Cloud-to-Local Email Handover (1:00-3:00)
1. **Trigger**: Send an email to the monitored account asking for an invoice.
2. **Cloud Detection**: Show `cloud-email-watcher` log detecting the email.
3. **Drafting**: Show `draft_reply.py` generating a response in the Cloud Vault.
4. **Sync**: Simulate/Show the file appearing in the Local Vault's `Pending_Approval` folder.
5. **Approval**: Move the file to `Approved`.
6. **Execution**: Show the Local Orchestrator picking up the approval and sending the email.

## Scenario 2: Odoo Accounting & CEO Briefing (3:00-5:00)
1. **Odoo Sync**: Run the `odoo-accounting` sync skill.
2. **Data**: Show the synced transactions in `AI_Employee_Vault/Accounting/`.
3. **Briefing**: Trigger the `ceo-briefing` generation.
4. **Result**: Review the "Monday Morning CEO Briefing" in Obsidian, showing revenue, bottlenecks, and cost-saving suggestions.

## Scenario 3: Ralph Wiggum Autonomous Loop (5:00-7:00)
1. **Task**: Drop a complex multi-step task file into `Needs_Action` (e.g., "Research 5 competitors, draft a social post for each, and prepare a comparison summary").
2. **Loop Start**: Show the orchestrator detecting a "suitable for Ralph" task.
3. **Persistence**: Show Claude working through multiple iterations, seeing its own state, and continuing until `TASK_COMPLETE` is reached.
4. **Completion**: Show the final summary in the `Done` folder.

## Scenario 4: Social Media Multi-Post (7:00-8:30)
1. **Command**: Use the `social-media-suite` skill to post to Twitter and LinkedIn.
2. **Approval**: Show the separate approval files created for each platform.
3. **Safety**: Approve Twitter but reject LinkedIn (to show flexibility).
4. **Live Check**: Show the successful post appearing on the platform.

## Conclusion (8:30-10:00)
- **Security**: Highlight that secrets stayed local and never synced to the cloud.
- **ROI**: Mention the 85-90% cost saving of a Digital FTE vs Human FTE.
- **Next Steps**: Inviting to the Wednesday Research Meeting.

---
*Digital FTE: The New Unit of Value*
