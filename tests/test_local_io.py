"""Tests for tools.local_io — file I/O helpers used by the Twinkle Hub agent.

Coverage:
- _safe_my_shared: accepts relative/absolute-inside-slot, blocks traversal.
- _failsafe: exceptions become "[ERROR] ..." strings (never raises into ADK).
- get_today_utc: returns valid JSON with compact + iso keys.
- save_curated_csv: writes CSV, handles bad JSON, preserves UTF-8.
- save_curated_json: writes pretty JSON, preserves Chinese.
- save_meta: writes sidecar with required fields + timestamp.
- list_curated: empty / non-existent / populated cases.
- read_curated: reads back, 200KB cap, missing file.
- load_local_tools: returns the 6 expected callables.
"""
from __future__ import annotations

import csv
import io
import json

import pytest

from tools.local_io import (
    _safe_my_shared,
    get_today_utc,
    list_curated,
    load_local_tools,
    read_curated,
    save_curated_csv,
    save_curated_json,
    save_meta,
)


# ----------------------------------------------------------- path safety

def test_safe_my_shared_accepts_relative(tmp_shared_root):
    target = _safe_my_shared("foo.csv")
    assert str(target).startswith(str(tmp_shared_root))
    assert target.name == "foo.csv"


def test_safe_my_shared_accepts_absolute_inside_slot(tmp_shared_root):
    """LLM sometimes echoes back the abs path from save_curated_csv; this
    must be tolerated as long as it's still inside the slot."""
    abs_path = str(tmp_shared_root / "bar.json")
    target = _safe_my_shared(abs_path)
    assert str(target) == abs_path


def test_safe_my_shared_rejects_traversal():
    with pytest.raises(ValueError, match="escapes shared slot"):
        _safe_my_shared("../escape.csv")


def test_safe_my_shared_rejects_absolute_outside_slot():
    with pytest.raises(ValueError, match="escapes shared slot"):
        _safe_my_shared("/etc/passwd")


def test_safe_my_shared_rejects_nested_traversal():
    with pytest.raises(ValueError, match="escapes shared slot"):
        _safe_my_shared("subdir/../../escape.csv")


# ----------------------------------------------------- get_today_utc

def test_get_today_utc_returns_json_with_compact_and_iso():
    result = get_today_utc()
    parsed = json.loads(result)
    assert set(parsed.keys()) == {"compact", "iso"}
    assert len(parsed["compact"]) == 8
    assert parsed["compact"].isdigit()
    assert "-" in parsed["iso"]
    assert len(parsed["iso"]) == 10


def test_get_today_utc_iso_and_compact_match():
    parsed = json.loads(get_today_utc())
    # compact is YYYYMMDD; iso is YYYY-MM-DD — same digits modulo hyphens
    assert parsed["compact"] == parsed["iso"].replace("-", "")


# ---------------------------------------------------- save_curated_csv

def test_save_curated_csv_basic(tmp_shared_root):
    rows = [["SP", 41746], ["RJ", 12852]]
    cols = ["state", "count"]
    path = save_curated_csv(json.dumps(rows), json.dumps(cols), "states.csv")
    assert "[ERROR]" not in path
    assert (tmp_shared_root / "states.csv").exists()
    content = (tmp_shared_root / "states.csv").read_text(encoding="utf-8")
    parsed = list(csv.DictReader(io.StringIO(content)))
    assert parsed == [
        {"state": "SP", "count": "41746"},
        {"state": "RJ", "count": "12852"},
    ]


def test_save_curated_csv_chinese_preserved(tmp_shared_root):
    rows = [["台北市", 100], ["新北市", 200]]
    cols = ["縣市", "件數"]
    save_curated_csv(json.dumps(rows, ensure_ascii=False),
                     json.dumps(cols, ensure_ascii=False), "zh.csv")
    raw = (tmp_shared_root / "zh.csv").read_text(encoding="utf-8")
    assert "台北市" in raw
    assert "縣市" in raw


def test_save_curated_csv_quotes_commas_newlines(tmp_shared_root):
    rows = [["a, b", 'has "quote"', "line1\nline2"]]
    cols = ["c1", "c2", "c3"]
    save_curated_csv(json.dumps(rows), json.dumps(cols), "tricky.csv")
    parsed = list(csv.DictReader(io.StringIO(
        (tmp_shared_root / "tricky.csv").read_text(encoding="utf-8")
    )))
    assert parsed == [{"c1": "a, b", "c2": 'has "quote"', "c3": "line1\nline2"}]


def test_save_curated_csv_invalid_rows_json():
    result = save_curated_csv("not valid json", '["c"]', "x.csv")
    assert result.startswith("[ERROR]") and "invalid JSON" in result


def test_save_curated_csv_invalid_columns_json():
    result = save_curated_csv("[]", "not valid", "x.csv")
    assert result.startswith("[ERROR]") and "invalid JSON" in result


def test_save_curated_csv_non_list_rows_json():
    result = save_curated_csv('{"a": 1}', '["c"]', "x.csv")
    assert result.startswith("[ERROR]") and "array of arrays" in result


def test_save_curated_csv_traversal_returns_error():
    """_safe_my_shared raises but _failsafe converts to ERROR string."""
    result = save_curated_csv("[]", "[]", "../escape.csv")
    assert result.startswith("[ERROR]") and "escapes shared slot" in result


def test_save_curated_csv_creates_parent_dir(tmp_shared_root):
    rows = [["a"]]
    cols = ["c"]
    save_curated_csv(json.dumps(rows), json.dumps(cols), "nested/dir/file.csv")
    assert (tmp_shared_root / "nested" / "dir" / "file.csv").exists()


# ---------------------------------------------------- save_curated_json

def test_save_curated_json_basic(tmp_shared_root):
    data = {"a": 1, "b": [2, 3]}
    path = save_curated_json(json.dumps(data), "data.json")
    assert "[ERROR]" not in path
    parsed = json.loads((tmp_shared_root / "data.json").read_text(encoding="utf-8"))
    assert parsed == data


def test_save_curated_json_chinese_unescaped(tmp_shared_root):
    """ensure_ascii=False so Chinese stays readable in the file."""
    data = {"地區": "台北", "件數": 1234}
    save_curated_json(json.dumps(data, ensure_ascii=False), "zh.json")
    raw = (tmp_shared_root / "zh.json").read_text(encoding="utf-8")
    assert "台北" in raw
    assert "\\u" not in raw


def test_save_curated_json_pretty_printed(tmp_shared_root):
    save_curated_json(json.dumps({"a": 1, "b": 2}), "pretty.json")
    raw = (tmp_shared_root / "pretty.json").read_text(encoding="utf-8")
    assert "\n  " in raw  # 2-space indent visible


def test_save_curated_json_invalid_input():
    result = save_curated_json("not json", "x.json")
    assert result.startswith("[ERROR]") and "invalid JSON" in result


# ----------------------------------------------------------- save_meta

def test_save_meta_writes_sidecar(tmp_shared_root):
    columns = ["a", "b", "c"]
    path = save_meta(
        csv_filename="data.csv",
        dataset_id="DS-001",
        dataset_name="Test Dataset",
        agency="Test Agency",
        domain="realestate",
        columns_json=json.dumps(columns),
        row_count=100,
        query="SELECT *",
        trace_id="trace-abc",
    )
    assert "[ERROR]" not in path
    assert path.endswith("data.csv.meta.json")
    meta = json.loads((tmp_shared_root / "data.csv.meta.json").read_text(encoding="utf-8"))
    assert meta["source_dataset_id"] == "DS-001"
    assert meta["name"] == "Test Dataset"
    assert meta["agency"] == "Test Agency"
    assert meta["domain"] == "realestate"
    assert meta["columns"] == columns
    assert meta["row_count"] == 100
    assert meta["query"] == "SELECT *"
    assert meta["trace_id"] == "trace-abc"
    assert meta["csv_filename"] == "data.csv"
    assert "fetched_at" in meta  # ISO timestamp


def test_save_meta_with_default_query_and_trace(tmp_shared_root):
    save_meta(
        csv_filename="data.csv",
        dataset_id="DS",
        dataset_name="N",
        agency="A",
        domain="D",
        columns_json="[]",
        row_count=0,
    )
    meta = json.loads((tmp_shared_root / "data.csv.meta.json").read_text(encoding="utf-8"))
    assert meta["query"] == ""
    assert meta["trace_id"] == ""


def test_save_meta_invalid_columns_json():
    result = save_meta(
        csv_filename="x.csv", dataset_id="d", dataset_name="n", agency="a",
        domain="d", columns_json="not json", row_count=0,
    )
    assert result.startswith("[ERROR]") and "invalid columns_json" in result


def test_save_meta_traversal_returns_error():
    result = save_meta(
        csv_filename="../escape.csv", dataset_id="d", dataset_name="n",
        agency="a", domain="d", columns_json="[]", row_count=0,
    )
    assert result.startswith("[ERROR]") and "escapes shared slot" in result


# ----------------------------------------------------------- list_curated

def test_list_curated_empty(tmp_shared_root):
    result = list_curated()
    assert result.startswith("[INFO]")
    assert "no files" in result


def test_list_curated_nonexistent_subdir(tmp_shared_root):
    result = list_curated("does-not-exist")
    assert result.startswith("[INFO]")
    assert "does not exist" in result


def test_list_curated_lists_files_with_sizes(tmp_shared_root):
    (tmp_shared_root / "a.csv").write_text("hello", encoding="utf-8")
    (tmp_shared_root / "b.json").write_text("[]", encoding="utf-8")
    result = list_curated()
    assert "a.csv" in result
    assert "b.json" in result
    assert "5 bytes" in result  # "hello" = 5 bytes
    assert "2 bytes" in result  # "[]"  = 2 bytes


def test_list_curated_subdir_filter(tmp_shared_root):
    sub = tmp_shared_root / "subdir"
    sub.mkdir()
    (sub / "x.csv").write_text("a", encoding="utf-8")
    (tmp_shared_root / "y.csv").write_text("a", encoding="utf-8")
    result = list_curated("subdir")
    assert "x.csv" in result
    assert "y.csv" not in result


# ----------------------------------------------------------- read_curated

def test_read_curated_basic(tmp_shared_root):
    (tmp_shared_root / "hello.txt").write_text("hello 世界", encoding="utf-8")
    result = read_curated("hello.txt")
    assert result == "hello 世界"


def test_read_curated_missing_file(tmp_shared_root):
    result = read_curated("nope.csv")
    assert result.startswith("[ERROR]") and "not found" in result


def test_read_curated_truncates_at_cap(tmp_shared_root, monkeypatch):
    import tools.local_io as local_io
    monkeypatch.setattr(local_io, "READ_BYTE_CAP", 10)
    (tmp_shared_root / "big.txt").write_text("a" * 100, encoding="utf-8")
    result = read_curated("big.txt")
    assert "TRUNCATED" in result
    assert "100 bytes" in result


def test_read_curated_traversal_returns_error():
    result = read_curated("../escape")
    assert result.startswith("[ERROR]") and "escapes shared slot" in result


# ----------------------------------------------------------- entry point

def test_load_local_tools_returns_six_callables():
    tools = load_local_tools()
    assert len(tools) == 6
    names = {t.__name__ for t in tools}
    assert names == {
        "get_today_utc",
        "save_curated_csv",
        "save_curated_json",
        "save_meta",
        "list_curated",
        "read_curated",
    }


# ----------------------------------------------------------- _failsafe contract

def test_failsafe_never_raises_on_bad_input():
    """A core contract — in-process FunctionTools must NEVER raise into ADK."""
    # Each user-facing tool wrapped by _failsafe should return string, not raise.
    assert isinstance(save_curated_csv("", "", "x.csv"), str)
    assert isinstance(save_curated_json("", "x.json"), str)
    assert isinstance(read_curated("../nope"), str)
    assert isinstance(list_curated("../nope"), str)
