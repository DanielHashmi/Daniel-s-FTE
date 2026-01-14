"""Unit tests for YAML parser utilities."""

import pytest
from src.utils.yaml_parser import (
    parse_frontmatter,
    serialize_frontmatter,
    validate_action_file_frontmatter,
    validate_plan_file_frontmatter,
    FrontmatterError
)


def test_parse_frontmatter_valid():
    """Test parsing valid YAML frontmatter."""
    content = """---
type: email
source: gmail
priority: high
---

Body content here
"""
    frontmatter, body = parse_frontmatter(content)

    assert frontmatter["type"] == "email"
    assert frontmatter["source"] == "gmail"
    assert frontmatter["priority"] == "high"
    assert "Body content here" in body


def test_parse_frontmatter_no_frontmatter():
    """Test parsing content without frontmatter."""
    content = "Just plain content"
    frontmatter, body = parse_frontmatter(content)

    assert frontmatter == {}
    assert body == content


def test_parse_frontmatter_invalid_yaml():
    """Test parsing invalid YAML raises error."""
    content = """---
invalid: yaml: content:
---

Body
"""
    with pytest.raises(FrontmatterError):
        parse_frontmatter(content)


def test_serialize_frontmatter():
    """Test serializing frontmatter and body."""
    frontmatter = {"type": "email", "priority": "high"}
    body = "Test body"

    result = serialize_frontmatter(frontmatter, body)

    assert "---" in result
    assert "type: email" in result
    assert "priority: high" in result
    assert "Test body" in result


def test_validate_action_file_frontmatter_valid():
    """Test validating valid action file frontmatter."""
    frontmatter = {
        "type": "email",
        "source": "gmail",
        "timestamp": "2026-01-14T10:30:00Z",
        "priority": "high",
        "status": "pending",
        "created_by": "watcher"
    }

    errors = validate_action_file_frontmatter(frontmatter)
    assert len(errors) == 0


def test_validate_action_file_frontmatter_missing_fields():
    """Test validation catches missing required fields."""
    frontmatter = {"type": "email"}

    errors = validate_action_file_frontmatter(frontmatter)
    assert len(errors) > 0
    assert any("Missing required field" in err for err in errors)


def test_validate_action_file_frontmatter_invalid_type():
    """Test validation catches invalid type value."""
    frontmatter = {
        "type": "invalid_type",
        "source": "gmail",
        "timestamp": "2026-01-14T10:30:00Z",
        "priority": "high",
        "status": "pending",
        "created_by": "watcher"
    }

    errors = validate_action_file_frontmatter(frontmatter)
    assert any("Invalid type" in err for err in errors)


def test_validate_plan_file_frontmatter_valid():
    """Test validating valid plan file frontmatter."""
    frontmatter = {
        "plan_id": "PLAN_001",
        "action_file": "EMAIL_gmail_2026-01-14T10-30-00.md",
        "created": "2026-01-14T10:35:00Z",
        "status": "draft",
        "priority": "high",
        "estimated_time": "15 minutes",
        "requires_approval": False
    }

    errors = validate_plan_file_frontmatter(frontmatter)
    assert len(errors) == 0


def test_validate_plan_file_frontmatter_invalid_requires_approval():
    """Test validation catches non-boolean requires_approval."""
    frontmatter = {
        "plan_id": "PLAN_001",
        "action_file": "EMAIL_gmail_2026-01-14T10-30-00.md",
        "created": "2026-01-14T10:35:00Z",
        "status": "draft",
        "priority": "high",
        "estimated_time": "15 minutes",
        "requires_approval": "yes"  # Should be boolean
    }

    errors = validate_plan_file_frontmatter(frontmatter)
    assert any("must be a boolean" in err for err in errors)
