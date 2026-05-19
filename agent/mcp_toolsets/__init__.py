"""MCP toolset loader for the Twinkle Hub agent.

ONE McpToolset only: the 3rd-party Twinkle Hub external HTTP MCP
(api.twinkleai.tw, Bearer auth via TWINKLE_HUB_API_KEY). This is the
single unavoidable MCP session — it is a 3rd-party server we do not
control and it only serves streamable-http, so it cannot be shimmed or
folded in-process.

The former local-saver MCP and the costaff-core extra MCP entry have
been removed: file I/O now runs in-process (agent/tools/local_io.py) and
the shared manager-core tools go via the costaff httpx shim
(agent/tools/costaff_api.py). That collapses Twinkle from 3+ concurrent
McpToolset sessions to exactly 1 — the dominant lever for the to_a2a
anyio cancel-scope race (project memory: single session ⇒ race≈0).
`TWINKLE_HUB_AGENT_MCP_URLS` is now intentionally ignored.
"""
import logging
import os
from typing import List

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    StreamableHTTPServerParams,
)

logger = logging.getLogger(__name__)

DEFAULT_TWINKLE_HUB_EXTERNAL_URL = "https://api.twinkleai.tw/mcp/"


def load_all_mcp_toolsets() -> List[McpToolset]:
    """Build the single external-hub McpToolset."""
    hub_url = os.getenv(
        "TWINKLE_HUB_EXTERNAL_MCP_URL", DEFAULT_TWINKLE_HUB_EXTERNAL_URL
    )
    hub_key = os.getenv("TWINKLE_HUB_API_KEY", "").strip()
    if not hub_key:
        logger.error(
            "TWINKLE_HUB_API_KEY is empty — Twinkle Hub MCP will fail "
            "Bearer auth. Set it in .env."
        )
    headers = {"Authorization": f"Bearer {hub_key}"} if hub_key else {}
    logger.info(
        f"Twinkle Hub external MCP (sole McpToolset): {hub_url} "
        f"(auth: {'bearer set' if hub_key else 'MISSING'})"
    )
    return [
        McpToolset(
            connection_params=StreamableHTTPServerParams(
                url=hub_url, headers=headers
            )
        )
    ]
