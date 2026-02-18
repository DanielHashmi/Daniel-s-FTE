"""Integration tests for email approval + MCP execution path."""

from src.handlers.local_approval import LocalApprovalHandler
from src.lib.vault import vault
from src.orchestration.approval_manager import ApprovalManager


class _FakeMcpResult:
    ok = True
    raw = {"result": {"content": [{"type": "text", "text": "ok"}]}}
    stdout = ""
    stderr = ""
    content_text = "ok"


def _set_temp_vault(workspace_tmp_dir):
    original = vault.root
    test_root = workspace_tmp_dir / "AI_Employee_Vault"
    vault.set_root(str(test_root))
    vault.ensure_structure()
    return original


def test_local_approval_handler_detects_markdown_cloud_draft(workspace_tmp_dir):
    original_root = _set_temp_vault(workspace_tmp_dir)
    try:
        draft = vault.dirs["pending_approval"] / "1700000000_EMAIL_act_demo.md"
        draft.write_text(
            "---\n"
            "type: approval_request\n"
            "action: send_email\n"
            "agent_role: cloud\n"
            "status: pending\n"
            "---\n\n"
            "# Email Draft\n\n"
            "## Content\n"
            "Draft body.\n",
            encoding="utf-8",
        )

        handler = LocalApprovalHandler(str(vault.root))
        drafts = handler.scan_pending_drafts()
        assert draft in drafts
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()


def test_approval_manager_send_email_calls_email_mcp(workspace_tmp_dir, monkeypatch):
    original_root = _set_temp_vault(workspace_tmp_dir)
    captured = {}

    def fake_call_node_mcp_tool(entrypoint, tool_name, arguments, timeout_seconds, env):
        captured["entrypoint"] = str(entrypoint)
        captured["tool_name"] = tool_name
        captured["arguments"] = arguments
        return _FakeMcpResult()

    monkeypatch.setattr(
        "src.orchestration.approval_manager.call_node_mcp_tool",
        fake_call_node_mcp_tool,
    )

    try:
        approved = vault.dirs["approved"] / "1700000000_EMAIL_send.md"
        approved.write_text(
            "---\n"
            "type: approval_request\n"
            "action: send_email\n"
            "to: client@example.com\n"
            "subject: \"Re: Update\"\n"
            "---\n\n"
            "# Email Draft\n\n"
            "## Content\n"
            "Approved email content.\n",
            encoding="utf-8",
        )

        manager = ApprovalManager()
        ok = manager.process_approved(approved)
        assert ok is True
        assert captured["tool_name"] == "send_email"
        assert captured["arguments"]["to"] == "client@example.com"
        assert captured["arguments"]["subject"] == "Re: Update"
        assert captured["arguments"]["text"] == "Approved email content."
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()
