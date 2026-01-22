---
name: social-media-suite
description: "WHAT: Post updates to Facebook, Instagram, and Twitter/X with platform-specific formatting. WHEN: User says 'post to facebook', 'tweet', 'instagram post', 'social media update'. Trigger on: multi-platform posting, brand visibility, lead generation, social scheduling."
---

# Social Media Suite

## When to Use
- Posting business updates to Facebook, Instagram, or Twitter
- Scheduling multi-platform content campaigns
- Checking post status across platforms
- Generating social media performance summaries

## Instructions

1. **Post to Facebook**:
   ```bash
   python3 .claude/skills/social-media-suite/scripts/main_operation.py --platform facebook --action post --message "YOUR_MESSAGE"
   ```
   *Supports: `--link URL` and `--image PATH`*

2. **Post to Instagram**:
   ```bash
   python3 .claude/skills/social-media-suite/scripts/main_operation.py --platform instagram --action post --image "PATH" --caption "CAPTION" --hashtags "#tag1,#tag2"
   ```
   *Note: Instagram requires an image for posts.*

3. **Post to Twitter/X**:
   ```bash
   python3 .claude/skills/social-media-suite/scripts/main_operation.py --platform twitter --action post --message "YOUR_MESSAGE"
   ```
   *Auto-truncates to 280 chars. Supports: `--image PATH`*

4. **Multi-Platform Post** (creates approval requests):
   ```bash
   python3 .claude/skills/social-media-suite/scripts/main_operation.py --platform all --action post --message "YOUR_MESSAGE" --image "PATH"
   ```
   *Creates separate approval files for each platform.*

5. **Check Post Status**:
   ```bash
   python3 .claude/skills/social-media-suite/scripts/main_operation.py --platform all --action status
   ```

6. **Weekly Summary** (for CEO Briefing):
   ```bash
   python3 .claude/skills/social-media-suite/scripts/main_operation.py --action summary --days 7
   ```

## Platform Character Limits
| Platform  | Limit | Notes |
|-----------|-------|-------|
| Facebook  | 63,206 | Links auto-expanded |
| Instagram | 2,200 | Requires image |
| Twitter   | 280 | Auto-truncates |

## Environment Variables Required
```bash
# Facebook/Instagram (Meta Graph API)
META_ACCESS_TOKEN=your_token
META_PAGE_ID=your_page_id
INSTAGRAM_BUSINESS_ID=your_ig_id

# Twitter/X
TWITTER_API_KEY=your_key
TWITTER_API_SECRET=your_secret
TWITTER_ACCESS_TOKEN=your_token
TWITTER_ACCESS_SECRET=your_secret
```

## Approval Workflow
All posts require HITL approval. Files created in:
`AI_Employee_Vault/Pending_Approval/SOCIAL_<platform>_<timestamp>.md`

## Validation
- [ ] Platform API authenticated
- [ ] Content within character limits
- [ ] Approval request created (if required)
- [ ] Post URL captured on success
- [ ] Audit log entry created

See [REFERENCE.md](./REFERENCE.md) for API setup guides.
