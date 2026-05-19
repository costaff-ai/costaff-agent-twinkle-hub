"""MCP toolset loader for the Twinkle Hub agent — now EMPTY.

Step 3 experiment (google/adk-python#5729): the agent holds ZERO global
`McpToolset`. The 3rd-party Twinkle Hub hub is reached per-request via
FunctionTools (agent/tools/twinkle_hub.py) that open and close their own
streamable-http MCP session strictly inside the awaited call body.
File I/O is in-process and the shared manager-core tools go via the
costaff httpx shim. Net: no streamable-http McpToolset under to_a2a at
all → the cancel-scope race cannot occur by construction; this A/Bs
against the Step-1 single-global-McpToolset build.

Kept as a stable entry point (returns []) so agent.py wiring is unchanged.
"""
from typing import List


def load_all_mcp_toolsets() -> List:
    """No global McpToolset — see module docstring / tools/twinkle_hub.py."""
    return []
