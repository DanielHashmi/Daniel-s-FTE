from pathlib import Path
from types import SimpleNamespace
import subprocess

from src.mcp.stdio_client import call_node_mcp_tool


def test_call_node_mcp_tool_marks_iserror_payload_as_failure(monkeypatch):
    stdout = (
        '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n'
        '{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"Error: spawn EPERM"}],"isError":true}}\n'
    )

    def fake_run(*args, **kwargs):
        return SimpleNamespace(stdout=stdout, stderr="", returncode=0)

    monkeypatch.setattr("src.mcp.stdio_client.subprocess.run", fake_run)

    result = call_node_mcp_tool(
        entrypoint=Path("mcp-servers/social-mcp/index.js"),
        tool_name="post_to_facebook",
        arguments={"content": "test"},
        timeout_seconds=5,
    )

    assert result.ok is False
    assert result.is_tool_error is True
    assert "Error:" in result.content_text


def test_call_node_mcp_tool_marks_error_prefix_content_as_failure(monkeypatch):
    stdout = (
        '{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"Error: simulated failure"}]}}\n'
    )

    def fake_run(*args, **kwargs):
        return SimpleNamespace(stdout=stdout, stderr="", returncode=0)

    monkeypatch.setattr("src.mcp.stdio_client.subprocess.run", fake_run)

    result = call_node_mcp_tool(
        entrypoint=Path("mcp-servers/social-mcp/index.js"),
        tool_name="post_to_facebook",
        arguments={"content": "test"},
        timeout_seconds=5,
    )

    assert result.ok is False
    assert result.is_tool_error is False
    assert "Error:" in result.content_text


def test_call_node_mcp_tool_requires_id2_tool_response(monkeypatch):
    stdout = (
        '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n'
    )

    def fake_run(*args, **kwargs):
        return SimpleNamespace(stdout=stdout, stderr="", returncode=0)

    monkeypatch.setattr("src.mcp.stdio_client.subprocess.run", fake_run)

    result = call_node_mcp_tool(
        entrypoint=Path("mcp-servers/social-mcp/index.js"),
        tool_name="post_to_facebook",
        arguments={"content": "test"},
        timeout_seconds=5,
    )

    assert result.ok is False
    assert result.raw == {}


def test_call_node_mcp_tool_timeout_with_tool_payload_treated_as_success(monkeypatch):
    stdout = (
        '{"jsonrpc":"2.0","id":1,"result":{"protocolVersion":"2024-11-05"}}\n'
        '{"jsonrpc":"2.0","id":2,"result":{"content":[{"type":"text","text":"Posted to Facebook! ID: 123"}]}}\n'
    )

    def fake_run(*args, **kwargs):
        exc = subprocess.TimeoutExpired(cmd="node", timeout=5, output=stdout, stderr="")
        # Keep explicit attributes for compatibility across Python versions.
        exc.stdout = stdout
        exc.stderr = ""
        raise exc

    monkeypatch.setattr("src.mcp.stdio_client.subprocess.run", fake_run)

    result = call_node_mcp_tool(
        entrypoint=Path("mcp-servers/social-mcp/index.js"),
        tool_name="post_to_facebook",
        arguments={"content": "test"},
        timeout_seconds=5,
    )

    assert result.ok is True
    assert result.is_tool_error is False
    assert "Posted to Facebook!" in result.content_text
