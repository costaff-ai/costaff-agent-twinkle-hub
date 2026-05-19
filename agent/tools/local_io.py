"""File I/O helper tools for the Twinkle Hub agent — IN-PROCESS.

Ported verbatim (logic-identical) from the old `mcp/tools/data_io.py`
that ran as the separate `costaff-mcp-twinkle-hub` MCP container. The
agent container already bind-mounts the same workspace
(`./workspace:/app/data`) with the same WORKSPACE/SHARED env, so these
write to the exact same path downstream agents read — but with ZERO
extra MCP session (the local-saver McpToolset is removed), which is the
dominant driver of the to_a2a anyio cancel-scope race (#5729/#4454).
"""
import csv
import functools
import json as json_lib
import os
from datetime import datetime, timezone
from pathlib import Path

COSTAFF_SHARED_DIR_TWINKLE_HUB = os.getenv(
    "COSTAFF_SHARED_DIR_TWINKLE_HUB",
    "/app/data/shared/costaff-agent-twinkle-hub",
)
READ_BYTE_CAP = 200_000  # avoid blowing the agent's context on read-back


def _failsafe(fn):
    """In-process FunctionTools must NOT raise — a raise propagates into
    ADK and aborts the whole A2A request (the old MCP server contained
    tool exceptions as result strings; we must too)."""
    @functools.wraps(fn)
    def w(*a, **k):
        try:
            return fn(*a, **k)
        except Exception as e:
            return f"[ERROR] {fn.__name__}: {e}"
    return w


def _ensure_dir(path: str) -> None:
    Path(path).mkdir(parents=True, exist_ok=True)


def _safe_my_shared(filename: str) -> Path:
    """Resolve under the agent's own shared slot, blocking traversal.

    Accepts an absolute path **iff it already resolves inside the shared
    slot** — the LLM naturally passes back the absolute path returned by
    save_curated_csv into save_meta; rejecting that outright is what
    triggered the abort. Anything resolving outside the slot still errors.
    """
    base = Path(COSTAFF_SHARED_DIR_TWINKLE_HUB).resolve()
    p = Path(filename)
    target = (p if p.is_absolute() else base / filename).resolve()
    if not target.is_relative_to(base):
        raise ValueError(f"path escapes shared slot: {filename}")
    return target


@_failsafe
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


@_failsafe
def save_curated_csv(rows_json: str, columns_json: str, filename: str) -> str:
    """Save query results as a CSV under the Twinkle Hub agent's shared slot.

    rows_json: JSON-encoded 2D array of values, e.g. '[["a","b"],["c","d"]]'.
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

    target = _safe_my_shared(filename)
    _ensure_dir(str(target.parent))

    with open(target, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(columns)
        writer.writerows(rows)
    return str(target)


@_failsafe
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

    target = _safe_my_shared(filename)
    _ensure_dir(str(target.parent))
    with open(target, "w", encoding="utf-8") as f:
        json_lib.dump(data, f, ensure_ascii=False, indent=2)
    return str(target)


@_failsafe
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

    Captures provenance so downstream agents (BA, Coding) know where the
    data came from and whether it's still fresh. The meta is written to
    '<csv_filename>.meta.json' in the same folder.

    Returns the absolute path of the meta file.
    """
    try:
        columns = json_lib.loads(columns_json)
    except json_lib.JSONDecodeError as e:
        return f"[ERROR] invalid columns_json: {e}"

    meta_target = _safe_my_shared(csv_filename + ".meta.json")
    _ensure_dir(str(meta_target.parent))

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


@_failsafe
def list_curated(subdir: str = "") -> str:
    """List files the Twinkle Hub agent has curated to its shared slot.

    subdir: optional relative subdirectory; empty = list everything.
    Returns one line per file: '<relpath> (<size> bytes)'.
    """
    base = Path(COSTAFF_SHARED_DIR_TWINKLE_HUB)
    target = _safe_my_shared(subdir) if subdir else base
    if not target.exists():
        return f"[INFO] '{target}' does not exist (nothing curated yet)"
    files = sorted(f for f in target.rglob("*") if f.is_file())
    if not files:
        return f"[INFO] no files under {target}"
    return "\n".join(
        f"{f.relative_to(base)} ({f.stat().st_size} bytes)" for f in files
    )


@_failsafe
def read_curated(filename: str) -> str:
    """Read back a previously-curated file (size-capped at 200 KB).

    Use sparingly — large reads burn agent context. Prefer returning
    paths to callers (BA, Coding) so they read with their own tools.

    filename: relative path under shared/costaff-agent-twinkle-hub/.
    """
    target = _safe_my_shared(filename)
    if not target.exists():
        return f"[ERROR] file not found: {target}"
    size = target.stat().st_size
    with open(target, "rb") as f:
        data = f.read(READ_BYTE_CAP)
    text = data.decode("utf-8", errors="replace")
    if size > READ_BYTE_CAP:
        text += f"\n\n[TRUNCATED: file is {size} bytes, showed first {READ_BYTE_CAP}]"
    return text


def load_local_tools() -> list:
    """The 6 file-I/O tools, in-process (no MCP session)."""
    return [get_today_utc, save_curated_csv, save_curated_json,
            save_meta, list_curated, read_curated]
