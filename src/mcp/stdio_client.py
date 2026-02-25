"""
MCP stdio client helpers.

Calls MCP servers over stdio using JSON-line requests + initialize handshake.
"""

from __future__ import annotations

import json
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional, List


def _project_root() -> Path:
    # src/mcp/stdio_client.py -> src/mcp -> src -> project root
    return Path(__file__).resolve().parents[2]


def _extract_json_objects(text: str) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not text:
        return out
    for line in text.splitlines():
        candidate = line.strip()
        if not candidate:
            continue
        if not (candidate.startswith("{") and candidate.endswith("}")):
            continue
        try:
            parsed = json.loads(candidate)
        except json.JSONDecodeError:
            continue
        if isinstance(parsed, dict):
            out.append(parsed)
    return out


def _coerce_text(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


@dataclass
class McpToolResult:
    ok: bool
    raw: Dict[str, Any]
    stdout: str
    stderr: str

    @property
    def content_text(self) -> str:
        """Best-effort text extraction from MCP 'content' field."""
        result = self.raw.get("result") if isinstance(self.raw, dict) else None
        if not isinstance(result, dict):
            return ""
        content = result.get("content")
        if isinstance(content, list) and content:
            first = content[0]
            if isinstance(first, dict):
                return str(first.get("text", ""))
        return ""

    @property
    def is_tool_error(self) -> bool:
        """True when MCP returned a tool-level error payload (`isError: true`)."""
        result = self.raw.get("result") if isinstance(self.raw, dict) else None
        if not isinstance(result, dict):
            return False
        return bool(result.get("isError"))


def _result_from_stdio_output(stdout_text: str, stderr_text: str) -> McpToolResult:
    responses = _extract_json_objects(stdout_text)
    if responses:
        payload = next((msg for msg in responses if msg.get("id") == 2), None)
        if payload is None:
            # Tool call response missing; don't treat initialize response as success.
            return McpToolResult(ok=False, raw={}, stdout=stdout_text, stderr=stderr_text)

        content_text = ""
        if isinstance(payload, dict):
            result_obj = payload.get("result")
            if isinstance(result_obj, dict):
                content = result_obj.get("content")
                if isinstance(content, list) and content:
                    first = content[0]
                    if isinstance(first, dict):
                        content_text = str(first.get("text", ""))

        tool_is_error = bool(
            isinstance(payload, dict)
            and isinstance(payload.get("result"), dict)
            and payload["result"].get("isError")
        )

        # Some servers report failures as successful JSON-RPC responses with
        # `result.isError=true`. Treat those as failures for callers.
        ok = bool(payload) and ("error" not in payload) and (not tool_is_error)

        # Defensive fallback for non-conformant servers that only return an
        # "Error: ..." message in content text.
        if ok and content_text.lower().startswith("error:"):
            ok = False
        return McpToolResult(ok=ok, raw=payload, stdout=stdout_text, stderr=stderr_text)

    return McpToolResult(ok=False, raw={}, stdout=stdout_text, stderr=stderr_text)


def call_node_mcp_tool(
    entrypoint: Path,
    tool_name: str,
    arguments: Dict[str, Any],
    timeout_seconds: int = 30,
    env: Optional[Dict[str, str]] = None,
) -> McpToolResult:
    """
    Call a Node MCP server tool using JSON-line stdio messages.

    Most local MCP servers in this repo accept plain JSON-RPC messages over stdin,
    one per line, and return JSON-RPC responses over stdout.
    """
    init_req = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "fte-local-executor", "version": "0.1.0"},
        },
    }
    initialized = {
        "jsonrpc": "2.0",
        "method": "initialized",
        "params": {},
    }
    call_req = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": tool_name, "arguments": arguments},
    }

    # Send one JSON message per line, newline-terminated. Some stdio transports
    # only flush/parse the last message when it ends with '\n'.
    request_stream = "\n".join(
        [
            json.dumps(init_req, separators=(",", ":")),
            json.dumps(initialized, separators=(",", ":")),
            json.dumps(call_req, separators=(",", ":")),
        ]
    ) + "\n"

    timeout = max(5, timeout_seconds)
    try:
        result = subprocess.run(
            ["node", str(entrypoint)],
            input=request_stream,
            text=True,
            capture_output=True,
            timeout=timeout,
            cwd=str(_project_root()),
            env=env,
        )
        stdout_text = _coerce_text(result.stdout)
        stderr_text = _coerce_text(result.stderr)
        return _result_from_stdio_output(stdout_text, stderr_text)
    except subprocess.TimeoutExpired as exc:
        # Some MCP stdio servers keep the process alive after emitting the tool
        # response. If we timed out but already received id=2, treat it as success.
        stdout_text = _coerce_text(exc.stdout)
        stderr_text = _coerce_text(exc.stderr)
        parsed = _result_from_stdio_output(stdout_text, stderr_text)
        if parsed.ok:
            return parsed

        timeout_note = f"[timeout after {timeout}s]"
        merged_stderr = f"{stderr_text}\n{timeout_note}" if stderr_text else timeout_note
        return McpToolResult(ok=False, raw=parsed.raw, stdout=stdout_text, stderr=merged_stderr)
