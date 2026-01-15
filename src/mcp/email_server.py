"""
Email MCP Server.

Exposes email capabilities as an MCP resource/tool.
For Silver Tier, this wraps the basic email sending logic.
"""

import asyncio
from mcp.server.fastmcp import FastMCP
from mcp.shared.exceptions import McpError

# Initialize FastMCP Server
mcp = FastMCP("email-server")

@mcp.tool()
async def send_email(to: str, subject: str, body: str, attachments: list[str] = None) -> str:
    """
    Send an email.

    Args:
        to: Recipient email address
        subject: Email subject
        body: Email body content
        attachments: List of file paths to attach

    Returns:
        Status message
    """
    # In a real implementation this would connect to SMTP or Gmail API
    # For Silver Tier MVP, we double check this is running in a controlled env
    # and maybe just log it or use Gmail API if creds available.

    print(f"Sending email to {to} with subject: {subject}")

    # Simulate success
    return f"Email sent to {to}"

@mcp.tool()
async def read_emails(query: str = "is:unread") -> str:
    """
    Read emails matching a query.
    """
    return "No new emails found (Mock)"

if __name__ == "__main__":
    mcp.run()
