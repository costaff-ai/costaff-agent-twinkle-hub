---
name: dataset-curation
description: >
  Generic discover-inspect-query-save workflow for any Twinkle Hub data
  request. Use as the default playbook for any task that asks me to
  "find / fetch / pull / get" a Taiwan open dataset, especially when the
  topic doesn't match a more specific skill (realestate-lookup,
  aqi-environment). Captures the lessons learned: English column names,
  DuckDB quoting, save+meta convention, retry policy.
---

# Dataset Curation Skill

The default workflow for fetching any Taiwan open dataset.

## When to use this skill

Trigger if the request asks me to fetch / find / pull / get / query /
analyze / curate Taiwan open data, AND a more specific topical skill
(`realestate-lookup`, `aqi-environment`) does NOT clearly apply.

## Workflow

### 0. Get today's date (one-time, before anything else)
- Call `get_today_utc()` once. Use the `compact` field (`YYYYMMDD`) for any filename date-stamp later in this task.
- Do NOT reuse a date from a different conversation — call the tool fresh each task.

### 1. Scope the request
Identify three things before any tool call:
- **Topic** → which Twinkle Hub `domain` is the most likely fit? (If unsure, call `opendata-list_domains` once.)
- **Output shape** → a few filtered rows (`query_rows`) or full dump (`materialize_dataset`)?
- **Time range / geography** → maps to SQL `WHERE` clauses.

### 2. Discover
- `opendata-search_datasets` with focused keywords + `domain` filter. Mandarin keywords usually hit better than English.
- If `count: 0`, drop the most restrictive filter (often `agency` or `domain`) and retry once before reporting failure.
- Pick 1 candidate. Prefer datasets with `is_normalised: true`, higher `quality_tier`, recent `update_freq`.

### 3. Inspect
- `opendata-get_dataset(dataset_id)` — record `schema.columns` (these are the **real** column names you must use in SQL), `row_count`, `update_freq`, `license`.
- If the dataset has **Chinese display column names** but English `schema.columns` (very common — e.g. `monitormonth` is real, `監測月份` is just a label), use the English ones in any SQL.

### 4. Query (preferred for filtered slices)
- `opendata-query_rows(dataset_id, where, columns=None, limit=100)`.
- **WHERE clause rules:**
  - No `WHERE` keyword in the parameter — just the predicate. e.g. `where="\"年度\" = '113' AND city = 'Taipei'"`.
  - Quote column names with double-quotes if they contain Chinese / special chars.
  - All values are strings (DuckDB `all_varchar=true`); use `=` with quoted strings, not numeric comparisons.
  - For ordering: append `ORDER BY ... DESC` to the `where` parameter (the gateway concatenates).
- If `query_invalid_sql` returns a Binder Error mentioning a column not found:
  1. Re-read `schema.columns` from step 3.
  2. Switch to the actual column name (likely English), retry once.
  3. If still failing, return the SQL + error to the caller — do not loop.

### 5. Materialize (only when needed)
- Use `opendata-materialize_dataset` only if:
  - The caller explicitly wants the full file, **or**
  - The dataset is small (< few MB by `get_dataset.row_count` × column count) and they need a complete CSV.
- Always `get_dataset` first — never materialize blind.

### 6. Save (always)
- `save_curated_csv(rows_json, columns_json, filename)` — pass the `rows` and `columns` arrays from `query_rows` response verbatim, JSON-encoded.
- `save_meta(...)` — immediately after save_curated_csv. Pass:
  - `dataset_id`, `dataset_name`, `agency`, `domain` from `get_dataset`.
  - `columns_json`, `row_count` from the actual saved file.
  - `query` = the WHERE clause used (empty string for materialize).
  - `trace_id` = the `_meta.opendata.trace_id` from the latest tool response.
- Filename convention: `<domain>__<dataset_id>__<TODAY_COMPACT>[__<slug>].csv`, where `<TODAY_COMPACT>` is the `compact` value from `get_today_utc()` (step 0).

### 7. Report
End with the structured contract from system.md:
- **Done** — 1 line.
- **Files** — absolute paths returned by `save_curated_csv` / `save_meta`.
- **Schema / row count**.
- **Caveats** — anything weird (column quirks, freshness gaps, license restrictions).

## Stop Condition (CRITICAL — avoid runaway over-fetching)

Stop searching and return as soon as ANY of these is true:

1. The first matching dataset's `query_rows` returns **≥ 10 rows** that satisfy the user's filter.
2. The user's request mentions a specific `dataset_id` and that dataset returns **any** rows.
3. 2 consecutive `search_datasets` calls have all returned datasets you've already considered (no new candidates).
4. You've already saved a CSV that matches the user's request — `list_curated()` shows it. Re-fetching is forbidden.

**Do NOT keep searching for a "better" or "more comprehensive" dataset** unless the caller explicitly says so (e.g. "find at least 3 sources for triangulation"). For typical analysis tasks, ONE good dataset is enough — the downstream BA Agent will tell the caller about data limitations in its report.

If the first dataset returns < 10 rows or no rows match the filter:
- Try **ONE** alternative search (broader keywords or sibling dataset).
- If that also yields < 10 rows, **stop and report**: "Limited data available: [details]. Saved [path]." Do not infinitely search.

**Per-task call budget**: in a single dispatch from the manager, do not exceed:
- 3 `search_datasets` calls
- 3 `get_dataset` calls
- 3 `query_rows` calls (across all datasets combined)

If you hit any budget cap and still don't have enough rows, return what you have with a clear "data sparse" note. The caller (manager) will decide whether to dispatch you again with different criteria.

---

## Anti-patterns

- ❌ Calling `materialize_dataset` before `get_dataset` — could pull GB of data unintentionally.
- ❌ Inlining rows into the response text — breaks composition with downstream agents and burns caller tokens.
- ❌ Using Chinese display labels in SQL — DuckDB Binder Error.
- ❌ Looping on the same SQL error more than 1 retry — stop and report the error verbatim.
- ❌ Inventing a date for the filename, or reusing one seen in earlier conversation — always call `get_today_utc()` fresh at the start of each task.
