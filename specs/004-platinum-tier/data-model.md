# Platinum Tier Data Model

## TaskFile (base entity)
| Field | Type | Description |
|-------|------|-------------|
| id | string | Unique task ID (timestamp-source)
| type | enum | 'cloud-email', 'local-payment', 'approval'
| status | enum | 'pending', 'in_progress', 'approved', 'rejected', 'done'
| domain | enum | 'cloud', 'local'
| created | datetime | ISO timestamp
| agent | string | 'cloud-agent', 'local-agent'

**Relationships**: Belongs to ApprovalRequest (if sensitive)

**State Transitions**:
pending → in_progress (claim-by-move) → approved/rejected → done

## ApprovalRequest
| Field | Type | Description |
|-------|------|-------------|
| task_id | string | References TaskFile.id |
| action | string | 'send_email', 'post_invoice'
| details | object | Action-specific params (recipient, amount)
| expires | datetime | TTL for approval

**Validation**: Human move to /Approved triggers execution

## CloudStatus
| Field | Type | Description |
|-------|------|-------------|
| uptime | float | % since last restart
| sync_lag | int | Seconds behind local vault
| queue_length | int | Pending tasks count
| last_sync | datetime | Last vault sync time