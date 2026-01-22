---
id: 0002
title: Research Python SDKs for Gold Tier Implementation
stage: general
date: 2026-01-19T00:00:00Z
surface: Claude Code Agent
model: claude-haiku-4-5-20251001
feature: 003-gold-tier
branch: 002-silver-tier
user: Daniel
command: N/A
labels: [research, sdk, gold-tier, xero, facebook, instagram, twitter]
links:
  spec: specs/003-gold-tier/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - path: docs/gold-tier-sdk-research.md
    status: created
    lines_added: 650
    lines_removed: 0
tests:
  - name: N/A
    status: N/A
    framework: N/A
---

## Prompt

Research the following Python SDKs and API clients for Gold Tier implementation:

1. **Xero SDK**: Find the official Python SDK for Xero accounting API
   - Package name and installation
   - OAuth 2.0 authentication pattern
   - Key capabilities (transactions, invoices, payments)
   - Rate limits and best practices

2. **Facebook SDK**: Find the official Python SDK for Facebook Graph API
   - Package name and installation
   - Authentication requirements
   - Posting capabilities and limitations

3. **Instagram SDK**: Find the official Python SDK for Instagram Graph API
   - Package name and installation
   - Authentication requirements (note: Instagram uses Facebook Graph API)
   - Posting capabilities (images, captions, hashtags)

4. **Twitter API Client**: Find the official or recommended Python client for Twitter API v2
   - Package name and installation
   - Authentication requirements (OAuth 2.0)
   - Tweet posting capabilities and character limits

For each SDK, provide:
- Official package name
- Installation command
- Basic authentication pattern
- Key methods for posting/syncing
- Rate limits
- Any important caveats or limitations

Format your findings as a structured report with sections for each SDK.

## Response snapshot

Conducted comprehensive research on Python SDKs for Gold Tier implementation covering Xero, Facebook, Instagram, and Twitter/X APIs. Used WebFetch tool to gather information from official repositories, documentation sites, and PyPI packages.

**Key Findings:**

1. **Xero SDK (xero-python)**: Official SDK available, OAuth 2.0 with 30-minute token expiration, supports Accounting/Assets/Files/Projects/Payroll APIs. Rate limits not publicly accessible without authorization.

2. **Facebook SDK**: Multiple options identified:
   - facebook-sdk (OUTDATED - avoid)
   - facebook-python-business-sdk (for advertising/marketing)
   - python-facebook-api (RECOMMENDED for general use)

3. **Instagram SDK**: No official standalone SDK. Must use Facebook Graph API via python-facebook or direct HTTP requests. Requires Business/Creator account and uses two-step posting process (container creation + publishing).

4. **Twitter/X SDK (Tweepy)**: Well-maintained official client, v4.16.0, supports API v2, comprehensive rate limit documentation (Free: 17 tweets/24hr, Basic: 100/24hr, Pro: 100/15min), OAuth 2.0 and OAuth 1.0a support.

Created comprehensive research report at `/mnt/c/Users/kk/Desktop/Daniel's FTE/docs/gold-tier-sdk-research.md` with detailed sections for each SDK including authentication patterns, code examples, rate limits, and implementation recommendations.

## Outcome

- ✅ Impact: Comprehensive SDK research completed for all four Gold Tier integrations (Xero, Facebook, Instagram, Twitter). Report provides actionable implementation guidance with code examples, authentication patterns, and rate limit information.
- 🧪 Tests: N/A (research activity)
- 📁 Files: Created docs/gold-tier-sdk-research.md (650+ lines)
- 🔁 Next prompts:
  1. Verify Xero rate limits via developer portal access
  2. Prototype Instagram two-step posting workflow
  3. Implement MCP servers for each SDK
  4. Integrate HITL approval workflow for all posting operations
- 🧠 Reflection: Research revealed Instagram has no official Python SDK and requires Facebook Graph API integration. Twitter/Tweepy is most mature and well-documented. Xero rate limits require authorized access to documentation. Facebook has multiple SDK options requiring careful selection based on use case.

## Evaluation notes (flywheel)

- Failure modes observed:
  1. WebSearch API errors (400 status) prevented initial search attempts
  2. Many documentation sites (developers.facebook.com, stackoverflow.com) blocked by WebFetch
  3. Xero rate limit documentation requires authorization
  4. Multiple GitHub repository searches returned 0 results
  5. Some PyPI pages inaccessible via WebFetch
- Graders run and results (PASS/FAIL): N/A
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): For future research tasks, start with direct repository/PyPI fetches rather than web search, as WebFetch proved more reliable than WebSearch for technical documentation.
