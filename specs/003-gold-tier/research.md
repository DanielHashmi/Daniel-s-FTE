# Research: Gold Tier Autonomous Employee

**Feature**: Gold Tier Autonomous Employee
**Date**: 2026-01-19
**Phase**: Phase 0 - Research & Technology Selection

## Overview

This document consolidates research findings for Gold Tier implementation, resolving all NEEDS CLARIFICATION items from the Technical Context. Research focused on three critical areas: (1) Python SDKs for external integrations, (2) watchdog process management, and (3) Ralph Wiggum loop pattern for persistent task execution.

---

## 1. Python SDKs for External Integrations

### 1.1 Xero Accounting SDK

**Decision**: Use `xero-python` (official Xero SDK)

**Installation**:
```bash
pip install xero-python
```

**Key Capabilities**:
- OAuth 2.0 authentication (30-minute access tokens, 60-day refresh tokens)
- Accounting API: invoices, payments, expenses, bank transactions
- Automatic token refresh support
- Supports Assets, Files, Projects, and Payroll APIs

**Authentication Pattern**:
```python
from xero_python.api_client import ApiClient
from xero_python.api_client.configuration import Configuration
from xero_python.api_client.oauth2 import OAuth2Token

config = Configuration()
api_client = ApiClient(
    oauth2_token=OAuth2Token(
        client_id=os.getenv("XERO_CLIENT_ID"),
        client_secret=os.getenv("XERO_CLIENT_SECRET")
    ),
    oauth2_token_saver=token_saver,
    oauth2_token_getter=token_getter
)
```

**Rate Limits**: Requires authorized developer portal access for specific limits. Implement exponential backoff for all API calls.

**Rationale**: Official SDK with active maintenance, OAuth 2.0 support, and comprehensive API coverage. Aligns with constitution requirement for secure credential management.

**Alternatives Considered**:
- **pyxero**: Community library, less actively maintained
- **Direct REST API**: More complex, no built-in token refresh

---

### 1.2 Facebook SDK

**Decision**: Use `python-facebook-api` (recommended community library)

**Installation**:
```bash
pip install --upgrade python-facebook-api
```

**Key Capabilities**:
- Facebook Graph API integration
- Instagram Business API support
- Three authentication methods (direct token, app-only, OAuth flow)
- Automatic pagination with `get_full_connections()`

**Authentication Pattern**:
```python
from pyfacebook import GraphAPI

api = GraphAPI(
    app_id=os.getenv("FACEBOOK_APP_ID"),
    app_secret=os.getenv("FACEBOOK_APP_SECRET"),
    access_token=os.getenv("FACEBOOK_ACCESS_TOKEN")
)
```

**Posting Method**:
```python
response = api.post_object(
    object_id="me",
    connection="feed",
    data={"message": "Post content"}
)
```

**Rate Limits**: Less transparent than Twitter. Implement rate limit detection and backoff.

**Rationale**: Most actively maintained Facebook SDK for Python. Supports both Facebook and Instagram APIs through single interface.

**Alternatives Considered**:
- **facebook-sdk**: Outdated (last updated 2018), Python 2.7 support
- **Direct Graph API**: More complex, no built-in pagination

---

### 1.3 Instagram SDK

**Decision**: Use Facebook Graph API via `python-facebook-api` (no official Instagram SDK exists)

**Critical Finding**: Meta does not provide a standalone Instagram Python SDK.

**Requirements**:
- Instagram Business or Creator account (cannot post to personal accounts via API)
- Facebook Page connected to Instagram account
- Images must be hosted at publicly accessible URLs

**Two-Step Posting Process**:
```python
# Step 1: Create media container
container = api.post_object(
    object_id=instagram_account_id,
    connection="media",
    data={
        "image_url": "https://example.com/image.jpg",
        "caption": "Post caption #hashtags"
    }
)

# Step 2: Publish container
api.post_object(
    object_id=instagram_account_id,
    connection="media_publish",
    data={"creation_id": container["id"]}
)
```

**Rationale**: Facebook Graph API is the official method for Instagram posting. Two-step process ensures content validation before publication.

**Alternatives Considered**:
- **instagram_simple_post**: Community library, requires Filestack for media hosting (additional dependency)
- **Direct Graph API**: Same complexity, no abstraction benefit

**Implementation Note**: More complex than other platforms. Recommend prototyping before full implementation.

---

### 1.4 Twitter SDK

**Decision**: Use `tweepy` v4.16.0+ (official Twitter SDK)

**Installation**:
```bash
pip install tweepy
# Or with async support
pip install tweepy[async]
```

**Key Capabilities**:
- Twitter API v1.1 and v2 support
- OAuth 2.0 Bearer Token and OAuth 2.0 with PKCE
- Built-in rate limit handling: `wait_on_rate_limit=True`
- Excellent documentation and active maintenance

**Authentication Pattern**:
```python
import tweepy

client = tweepy.Client(
    bearer_token=os.getenv("TWITTER_BEARER_TOKEN"),
    consumer_key=os.getenv("TWITTER_API_KEY"),
    consumer_secret=os.getenv("TWITTER_API_SECRET"),
    access_token=os.getenv("TWITTER_ACCESS_TOKEN"),
    access_token_secret=os.getenv("TWITTER_ACCESS_SECRET"),
    wait_on_rate_limit=True
)
```

**Posting Method**:
```python
response = client.create_tweet(text="Your tweet content")
```

**Rate Limits** (Well-Documented):
- **Free Tier**: 17 tweets/24 hours
- **Basic Tier**: 100 tweets/24 hours
- **Pro Tier**: 100 tweets/15 minutes

**Rationale**: Most mature and well-documented Twitter SDK. Built-in rate limit handling reduces implementation complexity. Active community support.

**Alternatives Considered**:
- **python-twitter**: Older library, less active maintenance
- **Direct Twitter API**: More complex, manual rate limit handling

---

### SDK Implementation Priority

1. **Twitter (Tweepy)** - Start here
   - Most straightforward implementation
   - Clear documentation and rate limits
   - Built-in rate limit handling

2. **Xero** - Second priority
   - Official SDK available
   - OAuth 2.0 well-documented
   - Critical for CEO Briefing feature

3. **Facebook** - Third priority
   - Multiple SDK options evaluated
   - python-facebook recommended
   - Rate limiting less transparent

4. **Instagram** - Most complex
   - No official SDK
   - Two-step posting workflow
   - Business account requirement
   - Prototype before full implementation

---

## 2. Watchdog Process Management

### Decision: Continue with PM2 (already implemented)

**Rationale**:
- **Already Operational**: System is configured with PM2 and working (`ecosystem.config.js` exists)
- **Cross-Platform**: Works on Linux, macOS, Windows (better than Supervisord)
- **Rich Tooling**: Built-in monitoring (`pm2 monit`), log management, process control
- **Node.js Already Required**: System uses Node.js v24.11.1 for Claude Code CLI
- **Active Development**: Large community, frequent updates
- **Existing Integration**: `/src/orchestration/watchdog.py` already integrates with PM2 via `pm2 jlist`

**Current Configuration** (`ecosystem.config.js`):
```javascript
{
  autorestart: true,
  max_memory_restart: "200M",
  max_restarts: 10,
  restart_delay: 4000,
  min_uptime: "10s",
  error_file: "AI_Employee_Vault/Logs/orchestrator-error.log",
  out_file: "AI_Employee_Vault/Logs/orchestrator-out.log"
}
```

**Alternatives Considered**:

**Supervisord**:
- **Pros**: Python-native, mature, lightweight (~20-30MB)
- **Cons**: Less active development, no built-in metrics, manual setup required
- **Verdict**: Not worth migration effort

**Custom Python Watchdog**:
- **Pros**: Full control, integrated with codebase, lightweight (~10-20MB)
- **Cons**: 2-3 weeks development time, testing burden, reinventing the wheel
- **Verdict**: Not justified for this use case

**Implementation Enhancements for Gold Tier**:

1. **WSL2 Auto-Start** (Windows Task Scheduler):
```xml
<Task>
  <Actions>
    <Exec>
      <Command>wsl</Command>
      <Arguments>-d Ubuntu -- bash -c "cd '/mnt/c/Users/kk/Desktop/Daniel'\''s FTE' && pm2 resurrect"</Arguments>
    </Exec>
  </Actions>
  <Triggers>
    <LogonTrigger />
  </Triggers>
</Task>
```

2. **Enhanced Health Checks** (extend existing `watchdog.py`):
```python
def check_health(self):
    # Check PM2 daemon is running
    if not self.is_pm2_running():
        self.logger.error("PM2 daemon not running")
        return False

    # Check all required processes
    process_status = self.get_process_status()
    for proc_name in self.required_processes:
        if proc_name not in process_status:
            self.restart_process(proc_name)
        elif process_status[proc_name] != "online":
            self.logger.warning(f"Process {proc_name} status: {process_status[proc_name]}")
```

3. **Dashboard Integration**:
```python
def get_pm2_metrics(self):
    result = subprocess.run(["pm2", "jlist"], capture_output=True, text=True)
    processes = json.loads(result.stdout)
    return {
        proc['name']: {
            'status': proc['pm2_env']['status'],
            'uptime': proc['pm2_env']['pm_uptime'],
            'restarts': proc['pm2_env']['restart_time'],
            'memory': proc['monit']['memory'],
            'cpu': proc['monit']['cpu']
        }
        for proc in processes
    }
```

---

## 3. Ralph Wiggum Loop Pattern

### Decision: Implement Stop hook with file-movement completion detection

**Overview**: The Ralph Wiggum loop is a Stop hook pattern that enables persistent task execution. When Claude tries to exit after completing a prompt, the Stop hook intercepts the exit and re-injects the prompt, allowing Claude to continue working until a multi-step task is truly complete.

**How It Works** (7-step cycle):
1. Orchestrator creates state file with initial prompt
2. Claude works on the task (executes one or more steps)
3. Claude attempts to exit (believes task is complete)
4. Stop hook intercepts the exit and checks completion criteria
5. If complete (task file in /Done/ OR completion promise) → Allow exit
6. If incomplete → Block exit, re-inject prompt, allow Claude to see previous output
7. Repeat until complete or maximum iterations reached

**Plugin Structure**:
```
.claude/
└── plugins/
    └── ralph-wiggum/
        ├── stop-hook.sh     # Bash script that intercepts exit
        └── config.json      # Configuration settings
```

**Configuration**:
```json
{
  "max_iterations": 10,
  "completion_strategy": "file_movement",
  "completion_promise": "TASK_COMPLETE",
  "timeout_per_iteration": 30,
  "state_file_path": ".claude/state/ralph-state.json"
}
```

**Completion Detection Methods**:

**Method 1: Promise-Based (Simple)**
- Claude outputs: `<promise>TASK_COMPLETE</promise>`
- Suitable for Bronze/Silver Tier
- Less reliable (Claude might forget)

**Method 2: File Movement (Advanced - Gold Tier Recommended)**
- Stop hook detects when task file moves from `/Needs_Action/` to `/Done/`
- More reliable - completion is natural part of workflow
- Orchestrator creates state file programmatically

**Rationale**: File-movement detection is more reliable and integrates naturally with existing workflow. Task completion = file in /Done/ folder, no special syntax required.

**Implementation Approach**:

**Stop Hook Script** (`stop-hook.sh`):
```bash
#!/bin/bash
# Check if task file has moved to Done/
STATE_FILE=".claude/state/ralph-state.json"
TASK_FILE=$(jq -r '.task_file' "$STATE_FILE")
ITERATION=$(jq -r '.iteration' "$STATE_FILE")
MAX_ITERATIONS=$(jq -r '.max_iterations' "$STATE_FILE")

# Check completion
if [ -f "AI_Employee_Vault/Done/$(basename $TASK_FILE)" ]; then
    echo "Task complete - file moved to Done/"
    exit 0
fi

# Check max iterations
if [ "$ITERATION" -ge "$MAX_ITERATIONS" ]; then
    echo "Max iterations reached - escalating to human"
    create_human_review_request
    exit 0
fi

# Increment iteration and re-inject prompt
jq ".iteration = $((ITERATION + 1))" "$STATE_FILE" > "$STATE_FILE.tmp"
mv "$STATE_FILE.tmp" "$STATE_FILE"
exit 1  # Block exit, continue loop
```

**Orchestrator Integration**:
```python
def start_ralph_loop(task_file_path, max_iterations=10):
    state = {
        "prompt": read_task_file(task_file_path),
        "iteration": 0,
        "max_iterations": max_iterations,
        "task_file": task_file_path,
        "completion_strategy": "file_movement"
    }
    write_state_file(state)
    invoke_claude_with_stop_hook()
```

**Best Practices**:
1. Prefer file movement over promises (more reliable)
2. Set appropriate max iterations (default 10, complex tasks 15-20)
3. Log each iteration with timestamp and actions (FR-005)
4. Handle HITL approval pauses (don't count against iteration limit)
5. Create human review request if max iterations reached (FR-007)

**Reference**: Internal documentation in hackathon guide (Section D: Persistence) and spec.md (User Story 1, FR-001 through FR-007). External reference (https://github.com/anthropics/claude-code/tree/main/.claude/plugins/ralph-wiggum) was not accessible.

---

## Security & Compliance Considerations

All SDK implementations must adhere to constitution requirements:

### Credential Management
- Store all API keys in environment variables
- Use OS-native secure storage for OAuth tokens (Keychain, Credential Manager)
- Implement token refresh mechanisms
- Never commit credentials to version control
- Maintain `.env` files in `.gitignore`

### Human-in-the-Loop
- All social media posting operations MUST create approval requests in `/Pending_Approval/`
- Financial transactions already covered by Silver Tier HITL
- No autonomous posting without explicit human approval

### Audit Logging
- Log every API call with timestamp, parameters, result, approval status
- Sanitize logs to exclude secrets and credentials (FR-043)
- Store logs in `/AI_Employee_Vault/Logs/YYYY-MM-DD.json`
- 90-day retention minimum (FR-045)

### Dry-Run Mode
- Implement for all SDKs during development
- Environment variable: `DRY_RUN=true`
- Log intended actions without executing

### Rate Limit Compliance
- Implement exponential backoff for all APIs
- Respect platform-specific rate limits
- Queue actions when limits reached
- Log rate limit events

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1-2)
1. Install and configure SDKs (`xero-python`, `python-facebook-api`, `tweepy`)
2. Implement OAuth 2.0 authentication for each platform
3. Create MCP servers for each SDK
4. Implement dry-run mode for all external actions

### Phase 2: Ralph Wiggum Loop (Week 2-3)
1. Create `.claude/plugins/ralph-wiggum/` directory structure
2. Implement `stop-hook.sh` with file-movement detection
3. Create `config.json` with default settings
4. Integrate with orchestrator for state file management
5. Add integration tests for multi-step task scenarios

### Phase 3: Watchdog Enhancements (Week 3)
1. Set up WSL2 auto-start using Windows Task Scheduler
2. Enhance `/src/orchestration/watchdog.py` with PM2 health checks
3. Add PM2 metrics to Dashboard.md
4. Configure log rotation in `ecosystem.config.js`
5. Add graceful shutdown handlers to Python processes

### Phase 4: Integration & Testing (Week 4)
1. End-to-end testing of each SDK integration
2. Test Ralph Wiggum loop with real multi-step tasks
3. Verify HITL approval workflow for all platforms
4. Load testing for rate limit handling
5. Security audit of credential management

---

## Open Questions & Risks

### Open Questions
1. **Xero Rate Limits**: Specific rate limits require authorized developer portal access. Contact Xero support if needed.
2. **Instagram Media Hosting**: Where to host images for Instagram posting? Options: AWS S3, Cloudinary, or local web server.
3. **Twitter API Tier**: Which tier is appropriate? Free (17 tweets/day) vs Basic ($100/month, 100 tweets/day)?

### Risks
1. **Instagram Complexity**: No official SDK increases implementation complexity. Recommend prototyping before full implementation.
2. **Rate Limit Variability**: Facebook/Instagram rate limits less transparent than Twitter. May require trial-and-error tuning.
3. **OAuth Token Expiration**: All platforms require token refresh. Must implement robust refresh logic to prevent service interruptions.
4. **Ralph Wiggum Loop Stability**: New pattern for this project. Requires thorough testing to ensure reliable autonomous operation.

---

## Conclusion

All NEEDS CLARIFICATION items from Technical Context have been resolved:

1. **Xero SDK**: `xero-python` (official)
2. **Facebook SDK**: `python-facebook-api` (recommended)
3. **Instagram SDK**: Use Facebook Graph API (no official SDK)
4. **Twitter SDK**: `tweepy` v4.16.0+ (official)
5. **Watchdog**: Continue with PM2 (already implemented)
6. **Ralph Wiggum Loop**: Stop hook with file-movement completion detection

Research findings provide clear implementation path for Gold Tier autonomous employee capabilities. All decisions align with constitution requirements for security, HITL approval, and audit logging.

**Next Phase**: Proceed to Phase 1 (Design & Contracts) to create data-model.md, contracts/interfaces.md, and quickstart.md.
