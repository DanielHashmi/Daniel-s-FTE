---
id: 0003
title: gold-tier-implementation-plan
stage: plan
date: 2026-01-19T00:00:00Z
surface: Claude Code CLI
model: claude-sonnet-4-5
feature: 003-gold-tier
branch: 003-gold-tier
user: system
command: /sp.plan
labels: [planning, gold-tier, autonomous-employee, xero-integration, social-media, ralph-wiggum-loop, ceo-briefing]
links:
  spec: specs/003-gold-tier/spec.md
  ticket: N/A
  adr: N/A
  pr: N/A
files:
  - path: specs/003-gold-tier/plan.md
    status: created
    lines: 221
  - path: specs/003-gold-tier/research.md
    status: created
    lines: 450
  - path: specs/003-gold-tier/data-model.md
    status: created
    lines: 520
  - path: specs/003-gold-tier/contracts/interfaces.md
    status: created
    lines: 580
  - path: specs/003-gold-tier/quickstart.md
    status: created
    lines: 650
  - path: CLAUDE.md
    status: updated
    lines: 11
tests:
  - N/A (planning stage)
---

## Prompt

User executed `/sp.plan` command to create implementation plan for Gold Tier Autonomous Employee specification.

Context: Gold Tier represents the evolution from functional assistant (Silver Tier) to fully autonomous business partner with:
- Ralph Wiggum loop for persistent multi-step task execution
- Xero accounting integration for financial intelligence
- Weekly CEO Briefing with business insights and proactive suggestions
- Comprehensive error recovery and graceful degradation
- Expanded social media (Facebook, Instagram, Twitter)
- Comprehensive audit logging
- Architecture documentation

Planning workflow executed:
1. Setup: Loaded spec.md and constitution.md
2. Technical Context: Identified NEEDS CLARIFICATION items (SDKs, watchdog, Ralph Wiggum loop)
3. Constitution Check: Validated all 8 principles (all PASS)
4. Phase 0 Research: Dispatched 3 parallel research agents
5. Phase 1 Design: Created data model, contracts, quickstart guide
6. Agent Context Update: Updated CLAUDE.md with new technologies
7. Post-Design Constitution Re-evaluation: Confirmed all principles satisfied

## Response snapshot

**Phase 0: Research (3 parallel agents)**

1. **SDK Research**: Evaluated Python SDKs for Xero, Facebook, Instagram, Twitter
   - Xero: `xero-python` (official SDK, OAuth 2.0)
   - Facebook: `python-facebook-api` (recommended community library)
   - Instagram: Use Facebook Graph API (no official SDK, two-step posting)
   - Twitter: `tweepy` v4.16.0+ (official, built-in rate limit handling)
   - Priority: Twitter → Xero → Facebook → Instagram (by complexity)

2. **Watchdog Research**: Compared PM2, Supervisord, Custom Python
   - Decision: Continue with PM2 (already implemented, cross-platform, rich tooling)
   - Enhancements: WSL2 auto-start, PM2 health checks, Dashboard integration
   - Rationale: No migration needed, proven in production

3. **Ralph Wiggum Loop Research**: Documented Stop hook pattern
   - 7-step cycle: create state → work → exit attempt → check completion → continue/exit
   - Two completion methods: file movement (recommended) vs promise-based
   - Configuration: max_iterations=10, file-movement detection
   - Implementation: `.claude/plugins/ralph-wiggum/` with stop-hook.sh

**Phase 1: Design & Contracts**

1. **Data Model** (7 core entities):
   - Task Execution State (Ralph loop state management)
   - Financial Transaction (Xero data structure)
   - CEO Briefing (weekly business intelligence report)
   - Audit Log Entry (comprehensive action logging)
   - Social Media Post (multi-platform posting)
   - Error Recovery Record (failure tracking and recovery)
   - Subscription Analysis (cost optimization)

2. **Contracts & Interfaces** (5 Agent Skills + 4 MCP servers):
   - Skills: /accounting-sync, /briefing-gen, /social-ops, /error-recovery, /audit-mgmt
   - MCP Servers: xero-mcp, facebook-mcp, instagram-mcp, twitter-mcp
   - Shared interfaces: audit logging, error recovery, HITL approval

3. **Quickstart Guide** (9-phase implementation):
   - Phase 1: Install dependencies (xero-python, python-facebook-api, tweepy)
   - Phase 2: Configure external APIs (OAuth 2.0 for all platforms)
   - Phase 3: Implement MCP servers
   - Phase 4: Implement Ralph Wiggum loop
   - Phase 5: Implement Agent Skills
   - Phase 6: Enhance watchdog
   - Phase 7: Create vault folders
   - Phase 8: Testing
   - Phase 9: Production deployment

**Constitution Check Results**:
- Pre-Design: All 8 principles PASS
- Post-Design: All 8 principles PASS (confirmed)
- No violations, no complexity tracking needed

## Outcome

- ✅ Impact: Created comprehensive implementation plan for Gold Tier with complete research, design, and deployment guide. Plan enables 40-60 hour implementation with clear priorities, technology decisions, and step-by-step instructions.
- 🧪 Tests: N/A (planning stage - test requirements defined in contracts/interfaces.md)
- 📁 Files: Created 5 files (plan.md: 221 lines, research.md: 450 lines, data-model.md: 520 lines, contracts/interfaces.md: 580 lines, quickstart.md: 650 lines), updated 1 file (CLAUDE.md: 11 lines)
- 🔁 Next prompts: `/sp.tasks` to generate task breakdown from plan, `/sp.implement` to execute implementation
- 🧠 Reflection: Planning successfully resolved all NEEDS CLARIFICATION items through parallel research agents. Design maintains full constitution compliance. Ralph Wiggum loop and CEO Briefing are signature Gold Tier features. SDK priority (Twitter → Xero → Facebook → Instagram) based on implementation complexity. PM2 decision avoids unnecessary migration. All design artifacts are production-ready.

## Evaluation notes (flywheel)

- Failure modes observed: None. Planning workflow completed successfully with parallel research agents.
- Graders run and results (PASS/FAIL): Constitution Check (Pre-Design): 8/8 PASS, Constitution Check (Post-Design): 8/8 PASS
- Prompt variant (if applicable): N/A
- Next experiment (smallest change to try): N/A
