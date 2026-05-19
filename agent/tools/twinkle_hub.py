"""External Twinkle Hub data tools — PER-REQUEST mcp-sdk client.

Experiment for google/adk-python#5729: instead of a global `McpToolset`
for the 3rd-party hub, each tool call opens its own streamable-http MCP
session strictly inside the awaited FunctionTool body (one task, entered
and exited in the same task) and tears it down before returning. This
is the maintainer's "don't hold McpToolset globally" pattern, adapted to
preserve precise tool args (Twinkle needs exact DuckDB SQL — a nested
nl-prompt sub-agent, as in the issue snippet, would lose that).

A/B vs the global-McpToolset Step-1 build measures whether per-request
construction also clears the residual `Failed to get tools from MCP
server` get_tools fragility (distinct from the anyio cancel-scope race
that single-session already fixed).

Tool names keep the hyphenated `opendata-*` form the skill/LLM expect.
Every wrapper is fail-safe (returns an [ERROR] string, never raises).
"""
import json
import logging
import os

from mcp import ClientSession
from mcp.client.streamable_http import streamablehttp_client

logger = logging.getLogger(__name__)

_HUB_URL = os.getenv(
    "TWINKLE_HUB_EXTERNAL_MCP_URL", "https://api.twinkleai.tw/mcp/"
)
_HUB_KEY = os.getenv("TWINKLE_HUB_API_KEY", "").strip()
_TIMEOUT = float(os.getenv("TWINKLE_HUB_CALL_TIMEOUT", "60"))
# A query_rows call with limit >= this AND no GROUP BY is treated as a
# "raw bulk pull" → the extraction guard appends a corrective. Small
# samples below this, and any aggregate (GROUP BY), are untouched.
_RAW_PULL_LIMIT = int(os.getenv("TWINKLE_HUB_RAW_PULL_LIMIT", "50"))


def _result_text(res) -> str:
    try:
        if getattr(res, "structuredContent", None):
            return json.dumps(res.structuredContent, ensure_ascii=False)
        parts = []
        for c in (getattr(res, "content", None) or []):
            t = getattr(c, "text", None)
            if t:
                parts.append(t)
        out = "\n".join(parts) if parts else str(res)
        if getattr(res, "isError", False):
            return f"[ERROR] {out}"
        return out
    except Exception as e:
        return f"[ERROR] could not parse hub result: {e}"


async def _call(tool: str, arguments: dict) -> str:
    """One self-contained streamable-http MCP session for a single call."""
    headers = {"Authorization": f"Bearer {_HUB_KEY}"} if _HUB_KEY else {}
    try:
        async with streamablehttp_client(
            _HUB_URL, headers=headers, timeout=_TIMEOUT
        ) as (read, write, _):
            async with ClientSession(read, write) as session:
                await session.initialize()
                res = await session.call_tool(tool, arguments)
        return _result_text(res)
    except Exception as e:
        logger.warning(f"[twinkle-hub] {tool} failed: {e!r}")
        return f"[ERROR] Twinkle Hub call {tool} failed: {e}"


async def search_datasets(query: str, domain: str = "", limit: int = 10) -> str:
    """Search Twinkle Hub for datasets. query: Mandarin keywords usually
    hit best. domain: optional Twinkle Hub domain key (e.g.
    'realestate_land', 'environment'). limit: max candidates."""
    args = {"query": query, "limit": limit}
    if domain:
        args["domain"] = domain
    return await _call("opendata-search_datasets", args)


async def get_dataset(dataset_id: str) -> str:
    """Inspect one dataset: returns schema.columns (the REAL column names
    to use in SQL), row_count, update_freq, license."""
    return await _call("opendata-get_dataset", {"dataset_id": dataset_id})


async def query_rows(
    dataset_id: str, where: str = "", columns: str = "", limit: int = 100
) -> str:
    """Run DuckDB SQL against a dataset for filtered / aggregated extraction.

    where: predicate only (no WHERE keyword); may end with GROUP BY /
        ORDER BY (the gateway concatenates). Quote Chinese column names
        with double quotes. All values are strings.
    columns: optional select-list expression (e.g. aggregates); empty = all.
    limit: row ceiling.
    """
    args = {"dataset_id": dataset_id, "limit": limit}
    if where:
        args["where"] = where
    if columns:
        args["columns"] = columns
    out = await _call("opendata-query_rows", args)

    # Option-2 semi-hard guard: a large raw pull (no GROUP BY, high
    # limit) is the non-representative-sample antipattern that broke the
    #房價走勢 task (skill prose alone got ignored). We do NOT block —
    # small samples (limit < _RAW_PULL_LIMIT) and proper aggregates
    # (GROUP BY present) pass untouched — but we append a strong,
    # deterministic corrective so the model self-corrects to an
    # aggregate query for trend/distribution/average analysis.
    is_agg = "group by" in (where or "").lower()
    if not is_agg and limit >= _RAW_PULL_LIMIT and not out.startswith("[ERROR]"):
        out += (
            f"\n\n[EXTRACTION GUARD] The above is a RAW row pull "
            f"(no GROUP BY, limit={limit}). For ANY trend / distribution "
            f"/ average / 比較 / by-month/by-區 analysis this is a "
            f"non-representative slice — you MUST instead re-query with "
            f"SQL aggregation: pass columns=\"<group-expr> AS k, "
            f"count(*) AS n, median(CAST(\\\"<num>\\\" AS DOUBLE)) AS "
            f"med\" and end `where` with `GROUP BY <group-expr> ORDER BY "
            f"<group-expr>`. Keep these raw rows ONLY if the task "
            f"genuinely wants individual records (a sample/lookup)."
        )
    return out


async def list_domains() -> str:
    """List the Twinkle Hub domains (call once if unsure which domain)."""
    return await _call("opendata-list_domains", {})


async def materialize_dataset(dataset_id: str) -> str:
    """Materialize a full dataset (use only for small datasets / explicit
    full-extract requests; always get_dataset first)."""
    return await _call("opendata-materialize_dataset", {"dataset_id": dataset_id})


# Keep the hyphenated names the skill/LLM expect (Gemini accepts hyphens;
# this is exactly how the McpToolset exposed them, so the A/B isolates
# ONLY the access pattern, not the tool surface).
search_datasets.__name__ = "opendata-search_datasets"
get_dataset.__name__ = "opendata-get_dataset"
query_rows.__name__ = "opendata-query_rows"
list_domains.__name__ = "opendata-list_domains"
materialize_dataset.__name__ = "opendata-materialize_dataset"


def load_twinkle_hub_tools() -> list:
    """External hub tools as per-request FunctionTools (zero McpToolset)."""
    return [search_datasets, get_dataset, query_rows,
            list_domains, materialize_dataset]
