# social-mcp

MCP server for social actions (Twitter/X, LinkedIn, Facebook, Instagram, WhatsApp).

## Facebook modes

`post_to_facebook` supports two execution modes:

- `FACEBOOK_POST_METHOD=graph_api` (default): uses Facebook Graph API token + page ID.
- `FACEBOOK_POST_METHOD=playwright`: calls `src/social/facebook_qwen_poster.py --mode post` and uses persistent browser session.

When `DRY_RUN=true`, tool calls are simulated.

## Required env (Graph API mode)

- `FACEBOOK_PAGE_TOKEN`
- `FACEBOOK_PAGE_ID`
- optional `META_GRAPH_API_VERSION` (default: `v19.0`)

## Required env (Playwright mode)

- `FACEBOOK_POST_METHOD=playwright`
- `FACEBOOK_COMPOSER_URL`
- `FACEBOOK_SESSION_DIR`
- optional `PYTHON_EXE`

## Instagram modes

`post_to_instagram` supports two execution modes:

- `INSTAGRAM_POST_METHOD=playwright` (default): calls `src/social/instagram_playwright_poster.py --mode post` and uses persistent browser session.
- `INSTAGRAM_POST_METHOD=graph_api`: uses Instagram Graph API credentials.

## Required env (Instagram Playwright mode)

- `INSTAGRAM_POST_METHOD=playwright`
- optional `INSTAGRAM_COMPOSER_URL` (default: `https://www.instagram.com/`)
- optional `INSTAGRAM_SESSION_DIR` (default: `instagram_session`)
- optional `INSTAGRAM_HEADLESS` (default: `false`)
- optional `INSTAGRAM_LOGIN_WAIT_SECONDS` (default: `600`)
- optional `INSTAGRAM_KEEP_OPEN_SECONDS` (default: `0`)
- optional `PYTHON_EXE`

## Required env (Instagram Graph API mode)

- `INSTAGRAM_POST_METHOD=graph_api`
- `INSTAGRAM_ACCESS_TOKEN`
- `INSTAGRAM_BUSINESS_ID`
- optional `META_GRAPH_API_VERSION` (default: `v19.0`)
- optional `INSTAGRAM_CONTAINER_MAX_ATTEMPTS` (default: `10`)
- optional `INSTAGRAM_CONTAINER_POLL_MS` (default: `2000`)

## WhatsApp Cloud API

`post_to_whatsapp` uses the official WhatsApp Cloud API send endpoint.

## Required env (WhatsApp Cloud API)

- `WHATSAPP_ACCESS_TOKEN`
- `WHATSAPP_PHONE_NUMBER_ID`
- optional `WHATSAPP_API_VERSION` (defaults to `META_GRAPH_API_VERSION`, then `v19.0`)

## Example tool inputs

- `post_to_facebook`: `{ "content": "Hello world" }`
- `post_to_instagram`: `{ "image_url": "https://example.com/pic.jpg", "caption": "Launch day!", "hashtags": "launch,startup" }`
- `post_to_whatsapp`: `{ "to": "+15551234567", "content": "Hello from Daniel's FTE", "preview_url": false }`
