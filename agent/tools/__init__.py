"""Native in-process function tools for the Twinkle Hub agent.

These replace two former MCP sessions (the local-saver MCP container and
the costaff-core extra MCP entry) with zero-MCP-session equivalents:
  - local_io      : file I/O, runs in-process (ported from old mcp/)
  - costaff_api   : 4 shared manager-core tools via the costaff httpx shim

Fewer concurrent McpToolset sessions ⇒ the to_a2a anyio cancel-scope
race drops toward zero (see project memory mcp-race-resolution). The
only remaining McpToolset is the unavoidable 3rd-party Twinkle Hub hub.
"""
from .costaff_api import load_costaff_api_tools
from .local_io import load_local_tools

__all__ = ["load_costaff_api_tools", "load_local_tools"]
