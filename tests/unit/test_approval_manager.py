"""Unit tests for approval execution safety and content extraction."""

from pathlib import Path

from src.lib.vault import vault
from src.orchestration.approval_manager import ApprovalManager


class _FakeMcpResult:
    ok = True
    raw = {"result": {"content": [{"type": "text", "text": "ok"}]}}
    stdout = ""
    stderr = ""
    content_text = "ok"


def test_extract_social_content_uses_only_content_section():
    manager = ApprovalManager()
    body = (
        "# Social Post Draft (facebook)\n\n"
        "## Content\n"
        "Line one\n"
        "Line two\n\n"
        "## Notes\n"
        "This should not be included\n"
    )

    extracted = manager._extract_social_content(body)
    assert extracted == "Line one\nLine two"


def test_process_approved_facebook_posts_exact_approved_content(workspace_tmp_dir, monkeypatch):
    original_root = vault.root
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
        test_vault = workspace_tmp_dir / "AI_Employee_Vault"
        vault.set_root(str(test_vault))
        vault.ensure_structure()

        approved_file = vault.dirs["approved"] / "test_facebook_approval.md"
        approved_file.write_text(
            "---\n"
            "type: approval_request\n"
            "action: social_post\n"
            "platform: facebook\n"
            "status: pending\n"
            "---\n\n"
            "# Social Post Draft (facebook)\n\n"
            "## Content\n"
            "Approved sentence A.\n"
            "Approved sentence B.\n\n"
            "## Extra\n"
            "Ignore this section.\n",
            encoding="utf-8",
        )

        manager = ApprovalManager()
        ok = manager.process_approved(approved_file)
        assert ok is True
        assert captured["tool_name"] == "post_to_facebook"
        assert captured["arguments"]["content"] == "Approved sentence A.\nApproved sentence B."
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()


def test_process_approved_facebook_uses_extended_timeout_budget(workspace_tmp_dir, monkeypatch):
    original_root = vault.root
    captured = {}

    monkeypatch.setenv("MCP_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("FACEBOOK_HEADLESS", "false")
    monkeypatch.setenv("FACEBOOK_LOGIN_WAIT_SECONDS", "600")
    monkeypatch.setenv("FACEBOOK_KEEP_OPEN_SECONDS", "45")
    monkeypatch.delenv("FACEBOOK_MCP_TIMEOUT_SECONDS", raising=False)

    def fake_call_node_mcp_tool(entrypoint, tool_name, arguments, timeout_seconds, env):
        captured["timeout_seconds"] = timeout_seconds
        captured["tool_name"] = tool_name
        captured["arguments"] = arguments
        return _FakeMcpResult()

    monkeypatch.setattr(
        "src.orchestration.approval_manager.call_node_mcp_tool",
        fake_call_node_mcp_tool,
    )

    try:
        test_vault = workspace_tmp_dir / "AI_Employee_Vault"
        vault.set_root(str(test_vault))
        vault.ensure_structure()

        approved_file = vault.dirs["approved"] / "test_facebook_timeout.md"
        approved_file.write_text(
            "---\n"
            "type: approval_request\n"
            "action: social_post\n"
            "platform: facebook\n"
            "status: pending\n"
            "---\n\n"
            "## Content\n"
            "Hello from timeout test.\n",
            encoding="utf-8",
        )

        manager = ApprovalManager()
        ok = manager.process_approved(approved_file)
        assert ok is True
        assert captured["tool_name"] == "post_to_facebook"
        assert captured["timeout_seconds"] == 735
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()


def test_process_approved_instagram_extracts_and_sanitizes_payload(workspace_tmp_dir, monkeypatch):
    original_root = vault.root
    captured = {}

    def fake_call_node_mcp_tool(entrypoint, tool_name, arguments, timeout_seconds, env):
        captured["tool_name"] = tool_name
        captured["arguments"] = arguments
        captured["timeout_seconds"] = timeout_seconds
        return _FakeMcpResult()

    monkeypatch.setattr(
        "src.orchestration.approval_manager.call_node_mcp_tool",
        fake_call_node_mcp_tool,
    )

    try:
        test_vault = workspace_tmp_dir / "AI_Employee_Vault"
        vault.set_root(str(test_vault))
        vault.ensure_structure()

        approved_file = vault.dirs["approved"] / "test_instagram_approval.md"
        approved_file.write_text(
            "---\n"
            "type: approval_request\n"
            "action: social_post\n"
            "platform: instagram\n"
            "status: pending\n"
            "image_url: \"https://example.com/photo.jpg\"\n"
            "---\n\n"
            "## Content\n"
            "Fresh product drop is live now.\n"
            "(Word count: 50, Character count: 300)\n\n"
            "## Hashtags\n"
            "launch growth #Startup\n",
            encoding="utf-8",
        )

        manager = ApprovalManager()
        ok = manager.process_approved(approved_file)

        assert ok is True
        assert captured["tool_name"] == "post_to_instagram"
        assert captured["arguments"]["image_url"] == "https://example.com/photo.jpg"
        assert "Word count" not in captured["arguments"]["caption"]
        assert captured["arguments"]["caption"].startswith("Fresh product drop is live now.")
        assert captured["arguments"]["hashtags"] == "#launch,#growth,#Startup"
    finally:
        vault.set_root(str(original_root))
        vault.ensure_structure()


def test_instagram_timeout_seconds_playwright_budget(monkeypatch):
    monkeypatch.setenv("MCP_TIMEOUT_SECONDS", "120")
    monkeypatch.setenv("INSTAGRAM_POST_METHOD", "playwright")
    monkeypatch.setenv("INSTAGRAM_HEADLESS", "false")
    monkeypatch.setenv("INSTAGRAM_LOGIN_WAIT_SECONDS", "600")
    monkeypatch.setenv("INSTAGRAM_KEEP_OPEN_SECONDS", "45")
    monkeypatch.delenv("INSTAGRAM_MCP_TIMEOUT_SECONDS", raising=False)

    manager = ApprovalManager()
    assert manager._instagram_timeout_seconds() == 765
