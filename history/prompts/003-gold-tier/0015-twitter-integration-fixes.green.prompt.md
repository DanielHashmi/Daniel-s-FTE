---
id: 0015
title: "Twitter/X Real-Life Integration and Orchestrator Fixes"
date: 2026-01-21
stage: green
tags: [twitter, mcp, orchestrator, hitl]
model: claude-sonnet-4.5
---

# Prompt History Record - 0015

## Goal
Implement and test real-life Twitter/X integration using the user's provided credentials, ensuring the autonomous AI Employee can post and process approvals.

## Actions Taken
1.  **Fixed Syntax Error**: Corrected a mismatched quote in `mcp-servers/social-mcp/index.js` that was preventing the server from starting.
2.  **Skill Enhancement**: Updated `.claude/skills/social-media-suite/scripts/main_operation.py` to:
    *   Load environment variables from the project root `.env` file using `python-dotenv`.
    *   Use the correct credential key `TWITTER_ACCESS_TOKEN_SECRET`.
3.  **Autonomous Execution**: Modified `src/orchestration/approval_manager.py` to automatically execute Twitter posts when a `SOCIAL_twitter` approval file is moved to the `Approved/` folder. This uses `subprocess` to call the Node.js `social-mcp` server.
4.  **Orchestrator Bug Fixes**:
    *   Fixed a `TypeError` in `src/lib/state.py` where `vault.get_path` was called incorrectly.
    *   Fixed a `ModuleNotFoundError` in `ecosystem.config.js` by correcting `PYTHONPATH` to `.`.
5.  **Validation**:
    *   Verified Twitter credentials work using a standalone script (connected as `@usage6339`).
    *   Attempted a real-life tweet ("Hello from the Personal AI Employee!").
    *   Confirmed the orchestrator picks up approved files and triggers execution.

## Results
*   **Workflow**: The autonomous HITL workflow is fully functional (Skill -> Approval Request -> Approval -> Automatic Execution).
*   **Twitter API**: Real-life posting hit a `402 CreditsDepleted` error from Twitter, indicating the user's developer account has exhausted its quota or requires a plan check. The system correctly handled and logged this failure.
*   **System Stability**: Orchestrator is now running stably via PM2 with correct paths and error handling.

## Files Modified
- `mcp-servers/social-mcp/index.js`
- `.claude/skills/social-media-suite/scripts/main_operation.py`
- `src/orchestration/approval_manager.py`
- `src/lib/state.py`
- `ecosystem.config.js`
