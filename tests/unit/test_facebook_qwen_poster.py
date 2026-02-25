"""Unit tests for Facebook Qwen poster helpers."""

from types import SimpleNamespace

import pytest

import src.social.facebook_qwen_poster as fb


def test_normalize_qwen_output_removes_wrappers():
    raw = """Here is your post:
```text
Facebook Post:
Hello world CTA
```
"""
    normalized = fb._normalize_qwen_output(raw)
    assert normalized == "Hello world CTA"


def test_build_qwen_prompt_includes_topic():
    prompt = fb.build_qwen_facebook_prompt("Announce product launch", "Initial idea")
    assert "Announce product launch" in prompt
    assert "Initial idea" in prompt
    assert "Output ONLY the final post text." in prompt


def test_generate_facebook_post_with_qwen_success(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=0, stdout="Facebook Post:\nGenerated post text", stderr="")

    monkeypatch.setattr(fb, "_resolve_qwen_path", lambda: "qwen")
    monkeypatch.setattr(fb.subprocess, "run", fake_run)

    result = fb.generate_facebook_post_with_qwen("Test prompt")
    assert result["success"] is True
    assert result["generated_content"] == "Generated post text"
    assert result["command"][0] == "qwen"


def test_generate_facebook_post_with_qwen_failure(monkeypatch):
    def fake_run(*args, **kwargs):
        return SimpleNamespace(returncode=1, stdout="", stderr="bad credentials")

    monkeypatch.setattr(fb, "_resolve_qwen_path", lambda: "qwen")
    monkeypatch.setattr(fb.subprocess, "run", fake_run)

    with pytest.raises(RuntimeError, match="Qwen CLI failed"):
        fb.generate_facebook_post_with_qwen("Test prompt")
