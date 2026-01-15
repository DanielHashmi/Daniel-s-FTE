# Data Model: Bronze Tier - Personal AI Employee Foundation

**Date**: 2026-01-14
**Feature**: 001-bronze-tier-foundation
**Phase**: Phase 1 - Design & Contracts

## Overview

This document defines the data structures and entities for the Bronze Tier Personal AI Employee system. All entities are stored as Markdown files with YAML frontmatter in the AI_Employee_Vault.

## Core Entities

### 1. Action File

**Purpose**: Represents a detected input that requires processing by Claude Code.

**Location**: `AI_Employee_Vault/Needs_Action/` (pending) → `AI_Employee_Vault/Done/` (completed)

**File Naming Convention**: `{TYPE}_{SOURCE}_{TIMESTAMP}.md`
- Example: `EMAIL_gmail_2026-01-14T10-30-00.md`
- Example: `FILE_inbox_2026-01-14T15-45-30.md`

**YAML Frontmatter Schema**:
```yaml
type: string              # "email" | "file" | "manual"
source: string            # "gmail" | "inbox" | "user"
timestamp: string         # ISO 8601 format: "2026-01-14T10:30:00Z"
priority: string          # "high" | "medium" | "low"
status: string            # "pending" | "processing" | "completed" | "error"
created_by: string        # "watcher" | "user"
processed_at: string?     # ISO 8601 timestamp when processed (optional)
error_message: string?    # Error details if status is "error" (optional)
```

**Markdown Body Structure**:
```markdown
## Content

[Original content: email snippet, file reference, or task description]

## Suggested Actions

- [ ] [Action 1]
- [ ] [Action 2]
- [ ] [Action 3]

## Notes

[Any additional context or metadata]
```

**Validation Rules**:
- `type` must be one of: "email", "file", "manual"
- `source` must be non-empty string
- `timestamp` must be valid ISO 8601 format
- `priority` must be one of: "high", "medium", "low"
- `status` must be one of: "pending", "processing", "completed", "error"
- File must have both frontmatter and body content

**State Transitions**:
```
pending → processing → completed
pending → processing → error
```

**Example**:
```markdown
---
type: email
source: gmail
timestamp: 2026-01-14T10:30:00Z
priority: high
status: pending
created_by: watcher
---

## Content

From: client@example.com
Subject: Urgent: Invoice Request

Hey, can you send me the invoice for January? Need it ASAP for accounting.

## Suggested Actions

- [ ] Generate invoice for January
- [ ] Send via email to client@example.com
- [ ] Log transaction in accounting system

## Notes

Client has requested invoices urgently in the past. High priority.
```

---

### 2. Plan File

**Purpose**: Represents Claude's proposed actions for handling an Action File.

**Location**: `AI_Employee_Vault/Plans/`

**File Naming Convention**: `PLAN_{ACTION_FILE_ID}_{TIMESTAMP}.md`
- Example: `PLAN_EMAIL_gmail_2026-01-14T10-30-00_2026-01-14T10-35-00.md`

**YAML Frontmatter Schema**:
```yaml
plan_id: string           # Unique identifier
action_file: string       # Reference to source action file
created: string           # ISO 8601 timestamp
status: string            # "draft" | "pending_approval" | "approved" | "rejected" | "completed"
priority: string          # Inherited from action file
estimated_time: string    # Human-readable estimate: "5 minutes", "1 hour"
requires_approval: boolean # true if any step needs human approval
approved_by: string?      # "human" if approved (optional)
approved_at: string?      # ISO 8601 timestamp (optional)
completed_at: string?     # ISO 8601 timestamp (optional)
```

**Markdown Body Structure**:
```markdown
## Objective

[Clear statement of what this plan aims to accomplish]

## Steps

1. [ ] [Step 1 description]
2. [ ] [Step 2 description]
3. [ ] [Step 3 description - REQUIRES APPROVAL]
4. [ ] [Step 4 description]

## Required Approvals

- Step 3: [Reason why approval needed]

## Estimated Completion Time

[Human-readable estimate]

## Notes

[Any additional context, risks, or considerations]
```

**Validation Rules**:
- `plan_id` must be unique
- `action_file` must reference existing action file
- `created` must be valid ISO 8601 format
- `status` must be one of: "draft", "pending_approval", "approved", "rejected", "completed"
- `requires_approval` must be boolean
- If `requires_approval` is true, must have "Required Approvals" section

**State Transitions**:
```
draft → pending_approval → approved → completed
draft → pending_approval → rejected
draft → completed (if no approval required)
```

**Example**:
```markdown
---
plan_id: PLAN_001
action_file: EMAIL_gmail_2026-01-14T10-30-00.md
created: 2026-01-14T10:35:00Z
status: draft
priority: high
estimated_time: 15 minutes
requires_approval: false
---

## Objective

Generate and prepare January invoice for client@example.com

## Steps

1. [x] Read client information from Company_Handbook.md
2. [x] Calculate invoice amount based on January work
3. [ ] Generate invoice PDF
4. [ ] Draft email with invoice attached
5. [ ] Move to Pending_Approval for human review

## Required Approvals

None (Bronze Tier does not send emails automatically)

## Estimated Completion Time

15 minutes

## Notes

Client has been flagged as high-priority in handbook. Invoice should be generated promptly.
```

---

### 3. Dashboard

**Purpose**: Real-time summary view of system status and activity.

**Location**: `AI_Employee_Vault/Dashboard.md`

**File Format**: Single Markdown file (no YAML frontmatter)

**Structure**:
```markdown
# AI Employee Dashboard

**Last Updated**: [ISO 8601 timestamp]

## System Status

- **Watcher**: [Running | Stopped | Error]
- **Watcher Type**: [Gmail | File System]
- **Last Check**: [ISO 8601 timestamp]
- **Uptime**: [Human-readable duration]

## Pending Actions

**Count**: [Number]

[List of pending action files with priority indicators]

## Recent Activity

[Last 10 activities with timestamps]

1. [Timestamp] - [Activity description]
2. [Timestamp] - [Activity description]
...

## Quick Stats

- **Files Processed Today**: [Count]
- **Files Processed This Week**: [Count]
- **Average Processing Time**: [Duration]
- **Success Rate**: [Percentage]

## Errors

[List of recent errors, if any]
```

**Update Frequency**: After each Claude processing run or watcher event

**Validation Rules**:
- Must have "Last Updated" timestamp
- System Status section must include watcher status
- Recent Activity must show most recent items first (reverse chronological)

**Example**:
```markdown
# AI Employee Dashboard

**Last Updated**: 2026-01-14T10:40:00Z

## System Status

- **Watcher**: Running
- **Watcher Type**: File System
- **Last Check**: 2026-01-14T10:39:45Z
- **Uptime**: 2 hours 15 minutes

## Pending Actions

**Count**: 3

- 🔴 HIGH: EMAIL_gmail_2026-01-14T10-30-00.md (Invoice request)
- 🟡 MEDIUM: FILE_inbox_2026-01-14T09-15-00.md (Contract review)
- 🟢 LOW: FILE_inbox_2026-01-14T08-00-00.md (Meeting notes)

## Recent Activity

1. 2026-01-14T10:35:00Z - Created plan for invoice request
2. 2026-01-14T10:30:15Z - Detected new email from client@example.com
3. 2026-01-14T09:15:30Z - Detected new file in Inbox
4. 2026-01-14T08:45:00Z - Completed processing of morning tasks
5. 2026-01-14T08:00:00Z - System started

## Quick Stats

- **Files Processed Today**: 5
- **Files Processed This Week**: 23
- **Average Processing Time**: 45 seconds
- **Success Rate**: 95%

## Errors

No recent errors.
```

---

### 4. Company Handbook

**Purpose**: Rule book defining how the AI should behave.

**Location**: `AI_Employee_Vault/Company_Handbook.md`

**File Format**: Single Markdown file (no YAML frontmatter)

**Structure**:
```markdown
# Company Handbook

**Last Updated**: [ISO 8601 timestamp]

## Communication Style

[Guidelines for how AI should communicate]

## Approval Thresholds

[Rules for when human approval is required]

## Priority Keywords

[Keywords that trigger high/medium/low priority]

## Error Handling Preferences

[How to handle different types of errors]

## Business Rules

[Domain-specific rules and preferences]
```

**Validation Rules**:
- Must have "Last Updated" timestamp
- All sections must be present
- Rules must be clear and actionable

**Example**:
```markdown
# Company Handbook

**Last Updated**: 2026-01-14T08:00:00Z

## Communication Style

- Always be polite and professional
- Use clear, concise language
- Avoid jargon unless necessary
- Address people by name when known

## Approval Thresholds

- **Always require approval**: Payments, new contacts, bulk operations
- **No approval needed**: Reading emails, creating plans, logging activities
- **Approval for amounts**: Any payment over $50

## Priority Keywords

**High Priority**:
- urgent, asap, critical, emergency, invoice, payment

**Medium Priority**:
- important, soon, review, feedback

**Low Priority**:
- fyi, info, update, note

## Error Handling Preferences

- **Network errors**: Retry 3 times with exponential backoff
- **Authentication errors**: Alert human immediately, pause operations
- **Parsing errors**: Log warning, attempt partial processing, create clarification request

## Business Rules

- Invoices should be generated within 24 hours of request
- Client emails should be acknowledged within 4 hours
- High-priority clients: client@example.com, vip@company.com
- Standard invoice payment terms: Net 30
```

---

### 5. Watcher (Abstract Interface)

**Purpose**: Background process that monitors input sources and creates Action Files.

**Implementation**: Python class (not a file entity)

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import List, Dict

class BaseWatcher(ABC):
    """Abstract base class for all watchers."""

    def __init__(self, vault_path: str, check_interval: int = 60):
        """
        Initialize watcher.

        Args:
            vault_path: Path to AI_Employee_Vault
            check_interval: Seconds between checks
        """
        self.vault_path = Path(vault_path)
        self.needs_action = self.vault_path / 'Needs_Action'
        self.check_interval = check_interval
        self.processed_ids = set()  # Track processed items

    @abstractmethod
    def check_for_updates(self) -> List[Dict]:
        """
        Check input source for new items.

        Returns:
            List of dicts with item metadata
        """
        pass

    @abstractmethod
    def create_action_file(self, item: Dict) -> Path:
        """
        Create action file in Needs_Action folder.

        Args:
            item: Item metadata from check_for_updates()

        Returns:
            Path to created action file
        """
        pass

    def run(self):
        """Main loop: check for updates and create action files."""
        pass
```

**State**:
- `vault_path`: Path to vault
- `check_interval`: Seconds between checks
- `processed_ids`: Set of already-processed item IDs

**Methods**:
- `check_for_updates()`: Query input source, return new items
- `create_action_file(item)`: Create Markdown file with YAML frontmatter
- `run()`: Main loop with error handling

---

### 6. Agent Skill (Abstract Interface)

**Purpose**: Reusable capability that performs a specific function.

**Implementation**: Python class (not a file entity)

**Interface Definition**:
```python
from abc import ABC, abstractmethod
from typing import Dict, Any

class BaseSkill(ABC):
    """Abstract base class for all Agent Skills."""

    name: str           # Skill identifier (e.g., "setup-vault")
    description: str    # Human-readable description
    version: str        # Semantic version (e.g., "1.0.0")

    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        """
        Execute the skill.

        Args:
            **kwargs: Skill-specific parameters

        Returns:
            Dict with 'status' (success/error) and 'message'
        """
        pass

    def validate_inputs(self, **kwargs) -> bool:
        """Validate required inputs before execution."""
        pass

    def dry_run(self, **kwargs) -> Dict[str, Any]:
        """Execute in dry-run mode (no side effects)."""
        pass
```

**Required Attributes**:
- `name`: Unique skill identifier
- `description`: What the skill does
- `version`: Semantic version

**Required Methods**:
- `execute(**kwargs)`: Perform the skill's function
- `validate_inputs(**kwargs)`: Check inputs before execution
- `dry_run(**kwargs)`: Test mode without side effects

**Return Format**:
```python
{
    "status": "success" | "error",
    "message": "Human-readable result",
    "data": {}  # Optional additional data
}
```

---

## Entity Relationships

```
Action File (1) ──creates──> (1) Plan File
Action File (N) ──updates──> (1) Dashboard
Watcher (1) ──creates──> (N) Action Files
Watcher (1) ──reads──> (1) Company Handbook
Claude Code (1) ──reads──> (N) Action Files
Claude Code (1) ──creates──> (N) Plan Files
Claude Code (1) ──updates──> (1) Dashboard
Claude Code (1) ──reads──> (1) Company Handbook
Agent Skill (N) ──manages──> (1) Watcher
Agent Skill (N) ──operates on──> (1) Vault
```

## Data Flow

```
1. Input arrives (email or file)
2. Watcher detects input
3. Watcher creates Action File in Needs_Action/
4. Watcher updates Dashboard
5. Claude Code reads Action Files
6. Claude Code reads Company Handbook for rules
7. Claude Code creates Plan File in Plans/
8. Claude Code moves Action File to Done/
9. Claude Code updates Dashboard
```

## Storage Considerations

**File System Layout**:
- All entities stored as Markdown files
- YAML frontmatter for structured metadata
- Human-readable format (can be edited manually)
- Git-friendly (text-based, line-by-line diffs)

**Concurrency**:
- File locking for write operations
- Atomic file moves (rename, not copy+delete)
- Timestamp-based conflict resolution

**Backup Strategy**:
- Vault is Git repository (version control)
- Daily commits of changes
- Logs rotated and archived

**Performance**:
- Small files (< 10KB each)
- Fast file system operations
- No database overhead
- Scales to thousands of files
