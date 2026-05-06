import os
from pathlib import Path
from mcp.server.fastmcp import FastMCP

WORKSPACE_DIR = os.getenv("WORKSPACE_DIR", "/app/data")
SHARED_DIR = os.getenv("SHARED_DIR", "/app/data/shared")
COSTAFF_SHARED_DIR_TWINKLE_HUB = os.getenv(
    "COSTAFF_SHARED_DIR_TWINKLE_HUB",
    "/app/data/shared/costaff-agent-twinkle-hub",
)

mcp = FastMCP(
    "twinkle-hub-mcp",
    host="0.0.0.0",
    port=int(os.getenv("MCP_TWINKLE_HUB_PORT", "8083")),
)


def ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def safe_my_shared(filename: str) -> Path:
    """Resolve filename under the agent's own shared slot, blocking traversal.

    filename: relative path under shared/costaff-agent-twinkle-hub/.
              Absolute paths and parent traversal (..) are rejected.
    """
    if filename.startswith("/"):
        raise ValueError(f"filename must be relative, got absolute: {filename}")
    base = Path(COSTAFF_SHARED_DIR_TWINKLE_HUB).resolve()
    target = (base / filename).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"path escapes shared slot: {filename}")
    return target
