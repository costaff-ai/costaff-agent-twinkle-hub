"""Auto-load `system.md` and provide a build_instruction() helper.

Usage:
    from instruction import build_instruction
    instruction = build_instruction()

Substitutes deployment-time placeholders ({WORKSPACE_DIR},
{SHARED_DIR_TWINKLE_HUB}, {user_id}, {PREFERRED_LANGUAGE}) with values
from environment variables. Falls back to a generic placeholder if
`system.md` is missing.

Runtime-varying values (today's date, current time) are intentionally
NOT substituted here — `build_instruction()` runs once at container
start, so any value resolved here would be frozen for the container's
lifetime. Such values are exposed as MCP tools instead (e.g.
`get_today_utc()`) and the agent calls them per task.
"""
import os
from pathlib import Path

_SYSTEM_PATH = Path(__file__).parent / "system.md"

if _SYSTEM_PATH.exists():
    instruction_content = _SYSTEM_PATH.read_text(encoding="utf-8")
else:
    instruction_content = "You are a helpful AI assistant."


def build_instruction() -> str:
    """Substitute deployment-time placeholders in the instruction template."""
    workspace_dir = os.getenv("WORKSPACE_DIR", "/app/data")
    preferred_lang = os.getenv("COSTAFF_PREFERRED_LANGUAGE", "English")
    shared_dir = os.getenv(
        "COSTAFF_SHARED_DIR_TWINKLE_HUB",
        "/app/data/shared/costaff-agent-twinkle-hub",
    )
    return (
        instruction_content
        .replace("{WORKSPACE_DIR}", workspace_dir)
        .replace("{SHARED_DIR_TWINKLE_HUB}", shared_dir)
        .replace("{user_id}", "shared")
        .replace("{PREFERRED_LANGUAGE}", preferred_lang)
    )
