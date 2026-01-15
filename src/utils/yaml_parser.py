"""YAML frontmatter parsing utilities."""

import re
from typing import Optional, Tuple
import yaml


class FrontmatterError(Exception):
    """Raised when frontmatter parsing fails."""
    pass


def parse_frontmatter(content: str) -> Tuple[dict, str]:
    """
    Extract YAML frontmatter and body from Markdown content.

    Args:
        content: Markdown content with optional YAML frontmatter

    Returns:
        Tuple of (frontmatter_dict, body_content)

    Raises:
        FrontmatterError: If frontmatter is malformed
    """
    # Match YAML frontmatter pattern: ---\n...\n---\n
    pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
    match = re.match(pattern, content, re.DOTALL)

    if not match:
        # No frontmatter found, return empty dict and full content
        return {}, content

    frontmatter_text = match.group(1)
    body = match.group(2)

    try:
        # Use safe_load to prevent code execution
        frontmatter = yaml.safe_load(frontmatter_text)
        if frontmatter is None:
            frontmatter = {}
        return frontmatter, body
    except yaml.YAMLError as e:
        raise FrontmatterError(f"Failed to parse YAML frontmatter: {e}")


def serialize_frontmatter(frontmatter: dict, body: str) -> str:
    """
    Serialize frontmatter dict and body into Markdown with YAML frontmatter.

    Args:
        frontmatter: Dictionary of frontmatter fields
        body: Markdown body content

    Returns:
        Complete Markdown content with frontmatter
    """
    if not frontmatter:
        return body

    yaml_text = yaml.dump(frontmatter, default_flow_style=False, sort_keys=False)
    return f"---\n{yaml_text}---\n{body}"


def validate_action_file_frontmatter(frontmatter: dict) -> list[str]:
    """
    Validate action file frontmatter against schema.

    Args:
        frontmatter: Frontmatter dictionary to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Required fields
    required_fields = ["type", "source", "timestamp", "priority", "status", "created_by"]
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    # Validate field values
    if "type" in frontmatter:
        valid_types = ["email", "file", "manual"]
        if frontmatter["type"] not in valid_types:
            errors.append(f"Invalid type: {frontmatter['type']}. Must be one of: {', '.join(valid_types)}")

    if "priority" in frontmatter:
        valid_priorities = ["high", "medium", "low"]
        if frontmatter["priority"] not in valid_priorities:
            errors.append(f"Invalid priority: {frontmatter['priority']}. Must be one of: {', '.join(valid_priorities)}")

    if "status" in frontmatter:
        valid_statuses = ["pending", "processing", "completed", "error"]
        if frontmatter["status"] not in valid_statuses:
            errors.append(f"Invalid status: {frontmatter['status']}. Must be one of: {', '.join(valid_statuses)}")

    if "created_by" in frontmatter:
        valid_creators = ["watcher", "user"]
        if frontmatter["created_by"] not in valid_creators:
            errors.append(f"Invalid created_by: {frontmatter['created_by']}. Must be one of: {', '.join(valid_creators)}")

    return errors


def validate_plan_file_frontmatter(frontmatter: dict) -> list[str]:
    """
    Validate plan file frontmatter against schema.

    Args:
        frontmatter: Frontmatter dictionary to validate

    Returns:
        List of validation error messages (empty if valid)
    """
    errors = []

    # Required fields
    required_fields = ["plan_id", "action_file", "created", "status", "priority", "estimated_time", "requires_approval"]
    for field in required_fields:
        if field not in frontmatter:
            errors.append(f"Missing required field: {field}")

    # Validate field values
    if "status" in frontmatter:
        valid_statuses = ["draft", "pending_approval", "approved", "rejected", "completed"]
        if frontmatter["status"] not in valid_statuses:
            errors.append(f"Invalid status: {frontmatter['status']}. Must be one of: {', '.join(valid_statuses)}")

    if "requires_approval" in frontmatter:
        if not isinstance(frontmatter["requires_approval"], bool):
            errors.append("requires_approval must be a boolean")

    return errors
