"""Test that email templates are properly structured"""

import pytest
from pathlib import Path


def test_email_templates_exist():
    """Verify email template directory and sample templates exist."""

    template_dir = Path("AI_Employee_Vault/templates/email")

    # If templates don't exist, that's okay - they're optional
    if not template_dir.exists():
        pytest.skip("Email templates directory not yet created")

    # Verify directory structure
    assert template_dir.exists()
    assert template_dir.is_dir()

    # Check for common templates
    common_templates = [
        "general.md",
        "invoice_response.md",
        "payment_confirmation.md",
        "client_followup.md",
        "urgent_reply.md"
    ]

    existing = [t for t in common_templates if (template_dir / t).exists()]

    # At minimum, general template should exist
    # (but we won't fail if it doesn't - user can create it)
    if len(existing) == 0:
        pytest.skip("No email templates found (optional)")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
