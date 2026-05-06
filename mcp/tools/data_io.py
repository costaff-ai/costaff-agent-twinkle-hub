"""File I/O + runtime helper tools for the Twinkle Hub Agent.

All writes land under the agent's own shared slot
(`/app/data/shared/costaff-agent-twinkle-hub/`), which downstream agents
(BA, Coding) read via the shared workspace convention.
"""
import csv
import json as json_lib
from datetime import datetime, timezone
from pathlib import Path

from core import (
    COSTAFF_SHARED_DIR_TWINKLE_HUB,
    ensure_dir,
    mcp,
    safe_my_shared,
)

READ_BYTE_CAP = 200_000  # avoid blowing the agent's context on read-back


@mcp.tool()
def get_today_utc() -> str:
    """Return today's date in UTC, in two ready-to-use formats.

    Returns a JSON object with:
    - 'compact': 'YYYYMMDD' (e.g. '20260506') — use as filename date-stamp.
    - 'iso':     'YYYY-MM-DD' (e.g. '2026-05-06') — use in human-readable text.

    Always call this at the start of any task that needs today's date.
    Never guess a date from training data, and never reuse a date from
    a previous conversation — those are stale.
    """
    now = datetime.now(timezone.utc)
    return json_lib.dumps({
        "compact": now.strftime("%Y%m%d"),
        "iso": now.strftime("%Y-%m-%d"),
    })


@mcp.tool()
def save_curated_csv(rows_json: str, columns_json: str, filename: str) -> str:
    """Save query results as a CSV under the Twinkle Hub agent's shared slot.

    rows_json: JSON-encoded 2D array of values, e.g. '[["a","b"],["c","d"]]'.
               Strings recommended (Twinkle Hub returns dtype=str by default).
    columns_json: JSON-encoded list of column names, e.g. '["col1","col2"]'.
    filename: relative path under shared/costaff-agent-twinkle-hub/.
              Convention: '<domain>__<dataset_id>__<YYYYMMDD>[__<slug>].csv'.

    Returns the absolute path of the written file.
    """
    try:
        rows = json_lib.loads(rows_json)
        columns = json_lib.loads(columns_json)
    except json_lib.JSONDecodeError as e:
        return f"[ERROR] invalid JSON input: {e}"

    if not isinstance(rows, list) or not isinstance(columns, list):
        return "[ERROR] rows_json must be a JSON array of arrays; columns_json a JSON array"

    target = safe_my_shared(filename)
    ensure_dir(str(target.parent))

    with open(target, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    return str(target)


@mcp.tool()
def save_curated_json(data_json: str, filename: str) -> str:
    """Save arbitrary JSON data under the Twinkle Hub agent's shared slot.

    Use for nested / non-tabular results (e.g. dataset metadata, list_domains
    output, or query results that aren't a flat 2D array).

    data_json: any valid JSON string.
    filename: relative path under shared/costaff-agent-twinkle-hub/.

    Returns the absolute path of the written file.
    """
    try:
        data = json_lib.loads(data_json)
    except json_lib.JSONDecodeError as e:
        return f"[ERROR] invalid JSON input: {e}"

    target = safe_my_shared(filename)
    ensure_dir(str(target.parent))
    with open(target, "w", encoding="utf-8") as f:
        json_lib.dump(data, f, ensure_ascii=False, indent=2)
    return str(target)


@mcp.tool()
def save_meta(
    csv_filename: str,
    dataset_id: str,
    dataset_name: str,
    agency: str,
    domain: str,
    columns_json: str,
    row_count: int,
    query: str = "",
    trace_id: str = "",
) -> str:
    """Write a sidecar metadata JSON next to a curated CSV.

    Captures provenance so downstream agents (BA, Coding) know where the data
    came from and whether it's still fresh.

    csv_filename: the curated CSV filename this meta belongs to (e.g.
                  'environment__28202__20260506.csv'). The meta is written
                  to '<csv_filename>.meta.json' in the same folder.
    dataset_id: Twinkle Hub dataset_id (e.g. '28202').
    dataset_name: human-readable name (e.g. '空氣品質監測月值').
    agency: source agency (e.g. '環境部').
    domain: Twinkle Hub domain key (e.g. 'environment').
    columns_json: JSON-encoded column names list.
    row_count: number of rows actually in the CSV.
    query: optional DuckDB SQL filter applied (empty string if full materialize).
    trace_id: optional Twinkle Hub trace_id from the _meta.opendata block.

    Returns the absolute path of the meta file.
    """
    try:
        columns = json_lib.loads(columns_json)
    except json_lib.JSONDecodeError as e:
        return f"[ERROR] invalid columns_json: {e}"

    meta_target = safe_my_shared(csv_filename + ".meta.json")
    ensure_dir(str(meta_target.parent))

    meta = {
        "source_dataset_id": dataset_id,
        "name": dataset_name,
        "agency": agency,
        "domain": domain,
        "columns": columns,
        "row_count": row_count,
        "query": query,
        "trace_id": trace_id,
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "csv_filename": csv_filename,
    }
    with open(meta_target, "w", encoding="utf-8") as f:
        json_lib.dump(meta, f, ensure_ascii=False, indent=2)
    return str(meta_target)


@mcp.tool()
def list_curated(subdir: str = "") -> str:
    """List files the Twinkle Hub agent has curated to its shared slot.

    Useful before re-fetching to check whether the same dataset/slice has
    already been saved this session.

    subdir: optional relative subdirectory under
            shared/costaff-agent-twinkle-hub/ (e.g. 'environment').
            Empty = list everything recursively.

    Returns one line per file: '<relpath> (<size> bytes)'.
    """
    base = Path(COSTAFF_SHARED_DIR_TWINKLE_HUB)
    target = safe_my_shared(subdir) if subdir else base
    if not target.exists():
        return f"[INFO] '{target}' does not exist (nothing curated yet)"
    files = sorted(f for f in target.rglob("*") if f.is_file())
    if not files:
        return f"[INFO] no files under {target}"
    return "\n".join(
        f"{f.relative_to(base)} ({f.stat().st_size} bytes)" for f in files
    )


@mcp.tool()
def read_curated(filename: str) -> str:
    """Read back a previously-curated file (size-capped).

    Use sparingly — large reads burn agent context. Prefer returning paths
    to callers (BA, Coding) so they read the file with their own tools.

    filename: relative path under shared/costaff-agent-twinkle-hub/.

    Returns the file content as text. If the file exceeds 200 KB, returns
    only the first 200 KB plus a truncation marker.
    """
    target = safe_my_shared(filename)
    if not target.exists():
        return f"[ERROR] file not found: {target}"
    size = target.stat().st_size
    with open(target, "rb") as f:
        data = f.read(READ_BYTE_CAP)
    text = data.decode("utf-8", errors="replace")
    if size > READ_BYTE_CAP:
        text += f"\n\n[TRUNCATED: file is {size} bytes, showed first {READ_BYTE_CAP}]"
    return text
