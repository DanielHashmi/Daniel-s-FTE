"""Integration tests for Platinum US1 offline email handover."""

from datetime import datetime

from src.lib.vault import vault
from src.orchestration.orchestrator import Orchestrator


class _FakeMcpResult:
    ok = True
    raw = {"result": {"content": [{"type": "text", "text": "ok"}]}}
    stdout = ""
    stderr = ""
    content_text = "ok"


class _FakeMcpErrorResult:
    ok = False
    is_tool_error = True
    raw = {"result": {"content": [{"type": "text", "text": "Error: simulated failure"}], "isError": True}}
    stdout = ""
    stderr = ""
    content_text = "Error: simulated failure"


def _set_temp_vault(workspace_tmp_dir):
    original = vault.root
    test_root = workspace_tmp_dir / "AI_Employee_Vault"
    vault.set_root(str(test_root))
    vault.ensure_structure()
    return original


def test_cloud_offline_cycle_creates_email_draft(workspace_tmp_dir, monkeypatch):
    original_root = _set_temp_vault(workspace_tmp_dir)
    try:
        action_id = "act_us1_cloud_email"
        content = (
            "---\n"
            f"id: \"{action_id}\"\n"
            "type: \"email\"\n"
            "source: \"gmail_watcher\"\n"
            "domain: \"personal\"\n"
            "priority: \"high\"\n"
            "timestamp: \"2026-02-15T00:00:00Z\"\n"
            "status: \"pending\"\n"
            "metadata:\n"
            "  sender: \"client@example.com\"\n"
            "  subject: \"Need response\"\n"
            "---\n\n"
            "Please send the updated details.\n"
        )
        vault.write_action(f"EMAIL_{action_id}.md", content, domain="personal")

        monkeypatch.setenv("AGENT_ROLE", "cloud")
        monkeypatch.setenv("AGENT_ID", "cloud-test-001")
        monkeypatch.setenv("STRICT_WORK_ZONES", "true")
        monkeypatch.setenv("WATCHER_GMAIL_ENABLED", "false")
        monkeypatch.setenv("WATCHER_LINKEDIN_ENABLED", "false")
        monkeypatch.setenv("WATCHER_ODOO_ENABLED", "false")

        orch = Orchestrator()
        orch.running = True
        orch.run_cycle()

        pending = vault.list_files_recursive("pending_approval", "*.md")
        assert pending, "Cloud role should create pending approval drafts for email actions"
        assert any(action_id in p.name for p in pending)
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()


def test_local_executes_approved_email_and_moves_to_done(workspace_tmp_dir, monkeypatch):
    original_root = _set_temp_vault(workspace_tmp_dir)
    called = {}

    def fake_call_node_mcp_tool(entrypoint, tool_name, arguments, timeout_seconds, env):
        called["tool_name"] = tool_name
        called["arguments"] = arguments
        return _FakeMcpResult()

    monkeypatch.setattr(
        "src.orchestration.approval_manager.call_node_mcp_tool",
        fake_call_node_mcp_tool,
    )

    try:
        approved_file = vault.dirs["approved"] / "1700000000_EMAIL_demo.md"
        approved_file.write_text(
            "---\n"
            "type: approval_request\n"
            "action: send_email\n"
            "to: client@example.com\n"
            "subject: \"Re: Need response\"\n"
            "domain: personal\n"
            "---\n\n"
            "# Email Draft\n\n"
            "## Content\n"
            "Approved response body.\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("AGENT_ROLE", "local")
        monkeypatch.setenv("AGENT_ID", "local-test-001")
        monkeypatch.setenv("STRICT_WORK_ZONES", "true")
        monkeypatch.setenv("WATCHER_WHATSAPP_ENABLED", "false")
        monkeypatch.setenv("WATCHER_BANKING_ENABLED", "false")
        monkeypatch.setenv("WATCHER_FILESYSTEM_ENABLED", "false")
        monkeypatch.setenv("WATCHER_ODOO_ENABLED", "false")

        orch = Orchestrator()
        orch.running = True
        orch.run_cycle()

        done_files = vault.list_files_recursive("done", "*.md")
        assert any(p.name == approved_file.name for p in done_files)
        assert called.get("tool_name") == "send_email"
        assert called.get("arguments", {}).get("text") == "Approved response body."

        log_file = vault.dirs["logs"] / f"{datetime.now().strftime('%Y-%m-%d')}.json"
        assert log_file.exists()
        assert "send_email" in log_file.read_text(encoding="utf-8", errors="ignore")
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()


def test_local_failed_approved_action_moves_to_recovery_queue(workspace_tmp_dir, monkeypatch):
    original_root = _set_temp_vault(workspace_tmp_dir)

    def fake_call_node_mcp_tool(entrypoint, tool_name, arguments, timeout_seconds, env):
        return _FakeMcpErrorResult()

    monkeypatch.setattr(
        "src.orchestration.approval_manager.call_node_mcp_tool",
        fake_call_node_mcp_tool,
    )

    try:
        approved_dir = vault.get_domain_dir("approved", "business")
        approved_dir.mkdir(parents=True, exist_ok=True)
        approved_file = approved_dir / "1700000001_SOCIAL_facebook_demo.md"
        approved_file.write_text(
            "---\n"
            "type: approval_request\n"
            "action: social_post\n"
            "platform: facebook\n"
            "domain: business\n"
            "---\n\n"
            "# Social Post Approval Request (facebook)\n\n"
            "## Content\n"
            "This should not retry endlessly.\n",
            encoding="utf-8",
        )

        monkeypatch.setenv("AGENT_ROLE", "local")
        monkeypatch.setenv("AGENT_ID", "local-test-001")
        monkeypatch.setenv("STRICT_WORK_ZONES", "true")
        monkeypatch.setenv("APPROVED_RETRY_ENABLED", "false")
        monkeypatch.setenv("WATCHER_WHATSAPP_ENABLED", "false")
        monkeypatch.setenv("WATCHER_BANKING_ENABLED", "false")
        monkeypatch.setenv("WATCHER_FILESYSTEM_ENABLED", "false")
        monkeypatch.setenv("WATCHER_ODOO_ENABLED", "false")

        orch = Orchestrator()
        orch.running = True
        orch.run_cycle()

        assert not approved_file.exists(), "Failed approved item should not remain in Approved/"
        recovery_files = vault.list_files_recursive("recovery_queue", "*.md")
        assert any("1700000001_SOCIAL_facebook_demo" in p.name for p in recovery_files)
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()
