---
title: Update Gold Tier Specs for Odoo 19
stage: refactor
date: 2026-01-20
---

# User Request
"update everything and make it entirley accurate also along with implementation update the documents and specs as well" (Context: Odoo integration status vs Xero specs)

# Context
The user identified a discrepancy where the specs referenced Xero but the implementation used Odoo (XML-RPC). Additionally, the project is set in 2026, where Odoo 19 is the current version and has deprecated XML-RPC in favor of JSON-2.

# Actions Taken
1.  **Analyzed Status**: Confirmed current date (Jan 2026), Odoo version (19), and protocol status (XML-RPC deprecated).
2.  **Updated Specs**:
    -   `specs/003-gold-tier/spec.md`: Swapped Xero for Odoo 19.
    -   `specs/003-gold-tier/data-model.md`: Updated Financial Transaction schema for Odoo IDs.
    -   `specs/003-gold-tier/tasks.md`: Renamed tasks from Xero to Odoo.
    -   `specs/003-gold-tier/plan.md`: Updated architecture decisions.
    -   `specs/003-gold-tier/quickstart.md`: Updated install/config steps for Odoo.
    -   `specs/003-gold-tier/contracts/interfaces.md`: Updated Agent Skill and MCP Server definitions.
3.  **Updated Config**: Added Odoo credentials to `.env.example`.
4.  **Updated Implementation**: Modified `.claude/skills/odoo-accounting/scripts/main_operation.py` docstrings to explicitly state Odoo 19 compatibility and the deprecation path for XML-RPC, ensuring "entire accuracy" about the code's current limitations.

# Key Decisions
-   **Protocol Choice**: Kept XML-RPC in code (for stability/simplicity) but documented it as "Legacy/Deprecated" in comments, rather than blind-refactoring to an undocumented JSON-2 format.
-   **Spec Alignment**: Fully aligned all design docs to Odoo to match the user's actual direction.

# Outcome
Project specs now accurately reflect the Odoo 19 integration strategy, and the codebase acknowledges its protocol status.
