"""
LinkedIn/Social MCP Server.

Exposes social media capabilities.
"""

import hashlib
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("social-server")

# Simple in-memory cache for dup detection (for MVP)
# In prod, use SQLite or file-based DB in Vault
POST_HISTORY = set()

@mcp.tool()
async def post_update(content: str) -> str:
    """
    Post an update to LinkedIn.
    """
    # 1. Duplicate detection
    content_hash = hashlib.md5(content.encode()).hexdigest()
    if content_hash in POST_HISTORY:
        return "Error: Duplicate content detected. Post rejected."

    # 2. Post logic (Mock for MVP)
    print(f"Posting to LinkedIn: {content}")

    # 3. Record history
    POST_HISTORY.add(content_hash)

    return "Posted successfully to LinkedIn"

if __name__ == "__main__":
    mcp.run()
