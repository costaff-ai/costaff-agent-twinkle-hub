import os

from core import mcp
import tools  # noqa: F401  (registers @mcp.tool() decorators on import)

if __name__ == "__main__":
    # Transport env-selectable. Default SSE: race-free under to_a2a()+
    # ADK1.33 (streamable-http anyio CancelScope race #4454 does NOT
    # occur on SSE — verified 2026-05-16). MCP_TRANSPORT=streamable-http
    # to switch back once ADK fixes #4454.
    mcp.run(transport=os.getenv("MCP_TRANSPORT", "sse"))
