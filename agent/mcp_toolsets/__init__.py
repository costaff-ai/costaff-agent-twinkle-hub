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
import re
from typing import List

from google.adk.tools.mcp_tool import McpToolset
from google.adk.tools.mcp_tool.mcp_session_manager import (
    SseConnectionParams,
    StreamableHTTPServerParams,
)

logger = logging.getLogger(__name__)

DEFAULT_TWINKLE_HUB_EXTERNAL_URL = "https://api.twinkleai.tw/mcp/"
DEFAULT_TWINKLE_HUB_LOCAL_URL = "http://costaff-mcp-twinkle-hub:8083/mcp"


def _server_params(url, headers=None):
    """ServerParams with transport chosen by MCP_TRANSPORT (default streamable-http).

    For MCP servers WE control (local saver, costaff-core). SSE is
    race-free under to_a2a()+ADK1.33 (#4454 does NOT occur on SSE —
    verified 2026-05-16). URL /mcp|/sse suffix normalised to transport.
    """
    t = os.getenv("MCP_TRANSPORT", "streamable-http").strip().lower()
    base = re.sub(r"/(mcp|sse)/?$", "", (url or "").rstrip("/"))
    if t == "streamable-http":
        return StreamableHTTPServerParams(url=base + "/mcp", headers=headers or {})
    return SseConnectionParams(url=base + "/sse", headers=headers or {})


def _connection_params(entry):
    """Coerce an entry (string URL or dict) into transport-correct ServerParams."""
    if isinstance(entry, str):
        url, headers = entry, None
    else:
        url = entry.get("url", "")
        headers = entry.get("headers") or None
    if not url:
        raise ValueError("MCP entry has no URL")
    return _server_params(url, headers)


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
    # EXTERNAL twinkle hub is a 3rd-party MCP (api.twinkleai.tw) we do NOT
    # control — it only serves streamable-http. This connection therefore
    # still uses streamablehttp_client and remains subject to the anyio
    # CancelScope race under to_a2a (#4454). Cannot be SSE'd from our side.
    toolsets.append(
        McpToolset(connection_params=StreamableHTTPServerParams(url=hub_url, headers=headers))
    )
    logger.info(
        f"Twinkle Hub external MCP: {hub_url} (auth: {'bearer set' if hub_key else 'MISSING'}) "
        f"[3rd-party streamable-http — race-prone, out of our control]"
    )

    # LOCAL saver MCP — ours, transport env-switchable (SSE default → race-free)
    local_url = os.getenv("MCP_TWINKLE_HUB_LOCAL_URL", DEFAULT_TWINKLE_HUB_LOCAL_URL)
    toolsets.append(
        McpToolset(connection_params=_server_params(local_url))
    )
    logger.info(
        f"Twinkle Hub local saver MCP: {local_url} "
        f"(transport={os.getenv('MCP_TRANSPORT','streamable-http')})"
    )

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
