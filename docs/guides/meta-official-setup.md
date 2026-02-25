# Meta Official API Setup (Instagram -> Facebook -> WhatsApp)

This guide uses the official Meta APIs already wired in this repo:

- Instagram Graph API publish path: `mcp-servers/social-mcp/index.js`
- Facebook Pages Graph API publish path: `mcp-servers/social-mcp/index.js`
- WhatsApp Cloud API send path: `mcp-servers/social-mcp/index.js`
- HITL execution: `src/orchestration/approval_manager.py`

All steps below assume date context February 18, 2026 and a local `.env` file at repo root.

## 1. Instagram First (Official Graph API)

1. In Meta for Developers, create/use a Business app.
2. In app products, add Instagram + Facebook Login/Pages.
3. Ensure your Instagram account is Professional (Business/Creator).
4. Link Instagram account to a Facebook Page.
5. Generate a user/page access token with Instagram publishing permissions.
6. Resolve your Instagram Business Account ID (the `INSTAGRAM_BUSINESS_ID` used by Graph API).
7. Update `.env`:

```env
INSTAGRAM_POST_METHOD=graph_api
INSTAGRAM_ACCESS_TOKEN=...
INSTAGRAM_BUSINESS_ID=...
META_GRAPH_API_VERSION=v19.0
INSTAGRAM_CONTAINER_MAX_ATTEMPTS=10
INSTAGRAM_CONTAINER_POLL_MS=2000
```

8. Start services:

```powershell
START_DASHBOARD.bat
START_BRAIN_LOCAL.bat
```

9. Verify account status:
- Open Dashboard -> Social and confirm Instagram shows connected in Graph mode.
- Or call `GET /api/social/accounts` and check `instagram.method=graph_api`.

10. Live validation:
- Create an Instagram post with a public `image_url` and caption.
- Approve it.
- Confirm successful publish message and check profile.

## 2. Facebook (Official Pages API)

1. Use the same Meta app (or another Business app).
2. Ensure the app has access to your target Page and required permissions.
3. Resolve `FACEBOOK_PAGE_ID` and Page Access Token.
4. Update `.env`:

```env
FACEBOOK_POST_METHOD=graph_api
FACEBOOK_PAGE_ID=...
FACEBOOK_PAGE_TOKEN=...
META_GRAPH_API_VERSION=v19.0
```

5. Validate in Dashboard -> Social: Facebook should show Graph API ready.
6. Create and approve a Facebook post.
7. Confirm returned post ID and page visibility.

## 3. WhatsApp (Official Cloud API)

1. In Meta app products, add WhatsApp.
2. Use test number flow first (Cloud API quickstart), then production number.
3. Collect:
- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
 - `WHATSAPP_VERIFY_TOKEN` (your webhook verify token)
4. Update `.env`:

```env
WHATSAPP_ACCESS_TOKEN=...
WHATSAPP_PHONE_NUMBER_ID=...
WHATSAPP_API_VERSION=v19.0
WHATSAPP_VERIFY_TOKEN=...
WHATSAPP_WEBHOOK_DOMAIN=personal
```

5. Configure webhook in Meta App -> WhatsApp:
- Callback URL: `https://<your-host>/api/webhooks/whatsapp`
- Verify token: same value as `WHATSAPP_VERIFY_TOKEN`
- Subscribe to message events needed by your workflow.
6. Validate in Dashboard -> Social: WhatsApp should show Cloud API ready.
7. Create a WhatsApp post in Social UI:
- Select WhatsApp platform
- Provide recipient in E.164 format (example: `+15551234567`)
- Enter message content
- Approve
8. Confirm delivery response (message ID) in execution output/logs.
9. Confirm inbound webhook ingestion:
- Send a WhatsApp text to the configured business/test number.
- Verify a new markdown file appears under `AI_Employee_Vault/Needs_Action/personal/` (or your configured webhook domain).

## 4. Safe Rollout Sequence

1. Keep `DRY_RUN=true` for first config validation.
2. Confirm all three accounts show connected in Social dashboard.
3. Set `DRY_RUN=false`.
4. Test single post per platform in this order:
- Instagram
- Facebook
- WhatsApp
5. Only after successful tests, run scheduled/autonomous posting.

## 5. Notes and Constraints

1. Instagram Graph API requires public media URL and professional account linkage.
2. WhatsApp Cloud API requires valid E.164 recipient format.
3. `auto_approve` social flow now supports WhatsApp in orchestrator.
4. Playwright config remains available as fallback for Facebook/Instagram if you switch `*_POST_METHOD=playwright`.
