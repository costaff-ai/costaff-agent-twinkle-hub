"""MCP toolset loader for the Twinkle Hub agent.

Loads three MCP toolsets:
    1. Twinkle Hub external HTTP MCP (data source — Bearer auth via
       TWINKLE_HUB_API_KEY, URL from TWINKLE_HUB_EXTERNAL_MCP_URL).
    2. Local saver MCP (file I/O for the shared workspace — URL from
       MCP_TWINKLE_HUB_LOCAL_URL, no auth, internal Docker network).
    3. Any extra MCP servers configured via TWINKLE_HUB_AGENT_MCP_URLS
       (set by the CoStaff manager at deploy time, e.g. manager core MCP).

TWINKLE_HUB_AGENT_MCP_URLS format (JSON):
    {
        "name": {"url": "...", "headers": {...}, "enabled": true,
                 "tool_filter": ["tool_a", "tool_b"]},
        ...
    }
"""
import json
import logging
import os
from typing import List

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import StreamableHTTPServerParams

logger = logging.getLogger(__name__)

DEFAULT_TWINKLE_HUB_EXTERNAL_URL = "https://api.twinkleai.tw/mcp/"
DEFAULT_TWINKLE_HUB_LOCAL_URL = "http://costaff-mcp-twinkle-hub:8083/mcp"


def _connection_params(entry):
    """Coerce an entry (string URL or dict) into StreamableHTTPServerParams."""
    if isinstance(entry, str):
        url, headers = entry, None
    else:
        url = entry.get("url", "")
        headers = entry.get("headers") or None
    if not url:
        raise ValueError("MCP entry has no URL")
    return StreamableHTTPServerParams(url=url, headers=headers or {})


def load_all_mcp_toolsets() -> List[McpToolset]:
    """Build the agent's MCP toolset list from env configuration."""
    toolsets: List[McpToolset] = []

    hub_url = os.getenv("TWINKLE_HUB_EXTERNAL_MCP_URL", DEFAULT_TWINKLE_HUB_EXTERNAL_URL)
    hub_key = os.getenv("TWINKLE_HUB_API_KEY", "").strip()
    if not hub_key:
        logger.error(
            "TWINKLE_HUB_API_KEY is empty — Twinkle Hub MCP will fail Bearer auth. Set it in .env."
        )
    headers = {"Authorization": f"Bearer {hub_key}"} if hub_key else {}
    toolsets.append(
        McpToolset(connection_params=StreamableHTTPServerParams(url=hub_url, headers=headers))
    )
    logger.info(
        f"Twinkle Hub external MCP: {hub_url} (auth: {'bearer set' if hub_key else 'MISSING'})"
    )

    local_url = os.getenv("MCP_TWINKLE_HUB_LOCAL_URL", DEFAULT_TWINKLE_HUB_LOCAL_URL)
    toolsets.append(
        McpToolset(connection_params=StreamableHTTPServerParams(url=local_url))
    )
    logger.info(f"Twinkle Hub local saver MCP: {local_url}")

    raw_extra = os.getenv("TWINKLE_HUB_AGENT_MCP_URLS", "")
    if raw_extra:
        try:
            extra_config = json.loads(raw_extra)
        except json.JSONDecodeError:
            logger.error("TWINKLE_HUB_AGENT_MCP_URLS is not valid JSON, skipping extra MCPs")
            return toolsets

        for name, entry in extra_config.items():
            if isinstance(entry, dict) and not entry.get("enabled", True):
                logger.info(f"Skipping disabled extra MCP: {name}")
                continue
            tool_filter = entry.get("tool_filter") if isinstance(entry, dict) else None
            try:
                toolsets.append(McpToolset(
                    connection_params=_connection_params(entry),
                    tool_filter=tool_filter,
                ))
                if tool_filter:
                    logger.info(f"Added extra MCP: {name} (filtered to {len(tool_filter)} tools: {tool_filter})")
                else:
                    logger.info(f"Added extra MCP: {name} (no filter — all tools imported)")
            except Exception as e:
                logger.error(f"Failed to load extra MCP '{name}': {e}")

    return toolsets
