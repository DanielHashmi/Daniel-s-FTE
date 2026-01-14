# Bronze Tier Agent Skills Catalog

**Version**: 1.0.0
**Date**: 2026-01-14
**Category**: Personal AI Employee - Bronze Tier Foundation

## Overview

This directory contains Claude Code Agent Skills for the Bronze Tier Personal AI Employee system. These skills provide reusable, documented capabilities for managing your AI Employee's vault, watchers, and processing workflows.

## Available Skills

### 1. setup-vault
**Purpose**: Initialize AI Employee Vault structure
**Status**: ✅ Ready
**File**: `setup-vault.md`

Creates the complete folder structure and initial files for the AI Employee Vault.

**Usage**:
```
User: "Run the setup-vault skill"
```

**Inputs**:
- `vault_path` (optional): Custom vault location
- `force` (optional): Overwrite existing vault

**Outputs**:
- Creates 8 folders (Inbox, Needs_Action, Done, Plans, Logs, etc.)
- Creates Dashboard.md, Company_Handbook.md, README.md
- Creates .gitignore for Obsidian compatibility

---

### 2. watcher-manager
**Purpose**: Start, stop, and manage watcher processes
**Status**: ✅ Ready
**File**: `watcher-manager.md`

Manages the lifecycle of watcher processes (File System or Gmail) using PM2.

**Usage**:
```
User: "Run watcher-manager with action=start"
User: "Run watcher-manager with action=stop"
User: "Run watcher-manager with action=status"
User: "Run watcher-manager with action=restart"
```

**Inputs**:
- `action` (required): "start", "stop", "restart", or "status"
- `watcher_type` (optional): "filesystem" or "gmail"
- `vault_path` (optional): Custom vault location

**Outputs**:
- Starts/stops watcher process with PM2
- Updates Dashboard.md with watcher status
- Shows process ID and uptime

---

### 3. process-inbox
**Purpose**: Process pending action files and create plans
**Status**: ✅ Ready
**File**: `process-inbox.md`

The "brain" of the AI Employee - reads action files, creates execution plans, updates dashboard.

**Usage**:
```
User: "Run process-inbox skill"
User: "Run process-inbox with priority_filter=high"
User: "Run process-inbox with dry_run=true"
```

**Inputs**:
- `vault_path` (optional): Custom vault location
- `priority_filter` (optional): "high", "medium", "low", or "all"
- `max_files` (optional): Maximum files to process
- `dry_run` (optional): Preview without changes

**Outputs**:
- Creates Plan.md files in Plans folder
- Moves processed files to Done folder
- Updates Dashboard.md with activity
- Generates processing summary

---

### 4. view-dashboard
**Purpose**: Display current system status and activity
**Status**: ✅ Ready
**File**: `view-dashboard.md`

Shows a formatted view of the AI Employee Dashboard with status, pending actions, and statistics.

**Usage**:
```
User: "Run view-dashboard skill"
User: "Run view-dashboard with format=summary"
User: "Run view-dashboard with format=status"
```

**Inputs**:
- `vault_path` (optional): Custom vault location
- `format` (optional): "full", "summary", or "status"
- `lines` (optional): Number of activity lines to show

**Outputs**:
- Formatted dashboard display
- System status indicators
- Pending actions summary
- Recent activity log
- Quick action suggestions

---

## Quick Start Workflow

### Initial Setup (First Time)

1. **Create Vault Structure**
   ```
   User: "Run the setup-vault skill"
   ```

2. **Open Vault in Obsidian**
   - Launch Obsidian
   - Open folder as vault → Select `AI_Employee_Vault`

3. **Customize Company Handbook**
   - Edit `AI_Employee_Vault/Company_Handbook.md`
   - Add your rules, priorities, and preferences

4. **Start Watcher**
   ```
   User: "Run watcher-manager with action=start"
   ```

5. **Verify System**
   ```
   User: "Run view-dashboard skill"
   ```

### Daily Usage

**Morning Check-In**:
```
User: "Show me the dashboard"
Claude: [Runs view-dashboard]

User: "Process any pending actions"
Claude: [Runs process-inbox]
```

**Add Manual Task**:
```
User: "Create a task to review quarterly report"
Claude: [Creates action file in Needs_Action]

User: "Process inbox"
Claude: [Runs process-inbox, creates plan]
```

**Check Status**:
```
User: "Is the watcher running?"
Claude: [Runs watcher-manager with action=status]
```

**Review Plans**:
```
User: "Show me the plans created today"
Claude: [Lists files in AI_Employee_Vault/Plans/]
```

### Troubleshooting

**Watcher Not Running**:
```
User: "Run watcher-manager with action=status"
User: "Run watcher-manager with action=start"
```

**Check for Errors**:
```
User: "Show me the dashboard"
Claude: [Displays errors section]

User: "Show me the watcher logs"
Claude: [Reads AI_Employee_Vault/Logs/watcher-*.log]
```

**Reset System**:
```
User: "Run watcher-manager with action=stop"
User: "Run setup-vault with force=true"
User: "Run watcher-manager with action=start"
```

## Skill Invocation Patterns

### Direct Invocation
```
User: "Run [skill-name] skill"
User: "Run [skill-name] with [param]=[value]"
User: "Run [skill-name] with [param1]=[value1] and [param2]=[value2]"
```

### Natural Language
```
User: "Set up the vault"
Claude: [Interprets as setup-vault skill]

User: "Start the watcher"
Claude: [Interprets as watcher-manager with action=start]

User: "Process my inbox"
Claude: [Interprets as process-inbox skill]

User: "Show me the dashboard"
Claude: [Interprets as view-dashboard skill]
```

### Chained Operations
```
User: "Set up the vault, then start the watcher, then show me the dashboard"
Claude: [Executes skills in sequence]
```

## Skill Development Guidelines

### Creating New Skills

When creating new skills for Bronze Tier, follow these guidelines:

1. **File Format**: Markdown (.md) in `.claude/skills/` directory
2. **Required Sections**:
   - Name, Version, Description, Category
   - Purpose
   - Inputs (with types and defaults)
   - Outputs
   - Prerequisites
   - Execution Steps
   - Example Usage
   - Error Handling
   - Testing
   - Version History

3. **Naming Convention**: Use kebab-case (e.g., `setup-vault`, `process-inbox`)

4. **Documentation**: Include clear examples and error messages

5. **Testing**: Provide test cases and validation steps

### Skill Template

```markdown
# [Skill Name] Skill

**Name**: skill-name
**Version**: 1.0.0
**Description**: Brief description
**Category**: Bronze Tier - Foundation

## Purpose
[What this skill does and why it's needed]

## Inputs
- `param1` (required): Description
- `param2` (optional): Description. Default: value

## Outputs
[What the skill produces]

## Prerequisites
[What must exist before running]

## Execution Steps
[Detailed steps with code/commands]

## Example Usage
[Real examples with expected results]

## Error Handling
[Common errors and solutions]

## Testing
[How to test the skill]

## Version History
- **1.0.0** (YYYY-MM-DD): Initial implementation
```

## Integration with Claude Code

These skills are designed to work seamlessly with Claude Code:

1. **Automatic Discovery**: Claude Code can discover skills in `.claude/skills/`
2. **Natural Language**: Users can invoke skills conversationally
3. **Parameter Passing**: Skills accept parameters via natural language
4. **Error Handling**: Skills provide clear error messages
5. **Chaining**: Skills can be chained together in workflows

## Skill Dependencies

```
setup-vault (no dependencies)
    ↓
watcher-manager (requires vault)
    ↓
process-inbox (requires vault + watcher)
    ↓
view-dashboard (requires vault)
```

## Performance Characteristics

| Skill | Execution Time | Memory Usage | Disk I/O |
|-------|---------------|--------------|----------|
| setup-vault | < 5 seconds | Minimal | Low (creates files) |
| watcher-manager | < 2 seconds | Minimal | None |
| process-inbox | 30-60s per file | Low | Medium (reads/writes) |
| view-dashboard | < 1 second | Minimal | Low (reads only) |

## Security Considerations

- **Credentials**: Never store credentials in skill files
- **Permissions**: Skills require write access to vault directory
- **Validation**: All inputs are validated before execution
- **Dry Run**: process-inbox supports dry-run mode for safety
- **Logging**: All actions are logged for audit trail

## Troubleshooting

### Skill Not Found

**Problem**: Claude says it can't find the skill

**Solutions**:
- Verify skill file exists in `.claude/skills/`
- Check file has `.md` extension
- Ensure skill name matches filename

### Skill Fails to Execute

**Problem**: Skill starts but fails during execution

**Solutions**:
- Check prerequisites are met
- Verify vault path is correct
- Review error messages in output
- Check logs in `AI_Employee_Vault/Logs/`

### Permission Denied

**Problem**: Cannot create files or folders

**Solutions**:
- Check write permissions on vault directory
- Verify disk space is available
- Run with appropriate user permissions

## Future Skills (Silver/Gold Tier)

Skills planned for future tiers:

**Silver Tier**:
- `send-email`: Send emails via MCP server
- `approve-action`: Approve pending actions
- `schedule-task`: Schedule recurring tasks
- `manage-contacts`: Manage contact list

**Gold Tier**:
- `generate-briefing`: Create CEO briefing
- `audit-accounting`: Run accounting audit
- `post-social`: Post to social media
- `analyze-metrics`: Analyze business metrics

## Contributing

To add new skills:

1. Create skill file in `.claude/skills/`
2. Follow skill template format
3. Test thoroughly
4. Update this catalog
5. Document in quickstart guide

## Support

- **Documentation**: See individual skill files for detailed docs
- **Issues**: Check logs in `AI_Employee_Vault/Logs/`
- **Community**: Join Wednesday research meetings

## Version History

- **1.0.0** (2026-01-14): Initial Bronze Tier skills
  - setup-vault
  - watcher-manager
  - process-inbox
  - view-dashboard

---

**Bronze Tier - Personal AI Employee Foundation**
*Building autonomous AI employees, one skill at a time.*
