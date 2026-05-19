---
name: realestate-lookup
description: >
  Pull Taiwan real-estate / 不動產 / 實價登錄 / 房價 / 地價 / 房屋交易 data.
  Use when the request mentions: 實價登錄, 房價, 房屋, 不動產, 建物, 地段,
  使用執照, 都市更新, real-estate, property, housing transaction. Maps to
  Twinkle Hub `realestate_land` domain. Most common downstream consumer
  is the Business Analysis Agent producing market reports.
---

# Real-Estate Lookup Skill

Specialized workflow for the `realestate_land` domain.

## When to use

Any task asking for Taiwan real-estate or land data:
- 實價登錄 / 成交價 / 房價中位數
- 建照 / 使用執照核發
- 都市更新案件
- 不動產經紀業 / 估價
- 地段 / 鄉鎮市區別交易量

## Common datasets in this domain

Search hits will vary, but the agencies to prefer are:
- **內政部不動產交易實價查詢服務** — quarterly transaction records, the canonical 實價登錄 source.
- **各直轄市政府地政局** — local supplementary data, building permits, urban renewal.
- **台北市 / 新北市 政府都市發展局** — building permits (使用執照).

## Extraction principle (decide BEFORE any query — this prevents slow over-fetching)

`limit` is a **safety ceiling, never the way you answer the question**.
First classify the request's intent, then the intent dictates the
strategy. Emit ONE plan line before the first `opendata-query_rows`:

> `plan: intent=<trend|sample|full> → strategy=<aggregate-SQL|limit N|materialize>; dataset=<id>; queries=<n>`

| Intent (keywords) | Strategy | What to send |
|---|---|---|
| **trend / 走勢 / 趨勢 / 分布 / 平均 / 中位數 / 比較 / by 月 / by 區** | **aggregate in SQL — never raw rows** | one `query_rows` whose `where` ends with `GROUP BY` + `ORDER BY`, selecting `median/avg/count`. Returns dozens of rows that cover the **whole** period. No meaningful `limit` (set it high, e.g. 5000, purely as a ceiling). |
| **sample / 看長相 / 幾筆範例 / 某一筆** | small `limit` (10–50) | a plain filtered `query_rows` — small IS correct here. |
| **full / 整包資料給下游 / 完整 CSV** | `materialize_dataset` (paginates to completeness) | never a capped `query_rows`. |

The old failure: pulling `limit=500` raw rows for a "房價走勢" request
analyses a non-representative slice. A 2-year district trend is
thousands of rows; the **aggregate** path returns ~24 monthly rows that
represent all of them.

### Plan first, then batch (don't explore-as-you-go)

1. `search_datasets` once → pick the dataset.
2. `get_dataset` once → read `schema.columns`. **Confirm schema only once**; do not re-`get_dataset` the same id.
3. Decide ALL the queries you need up front. If they are independent
   (e.g. several districts, or raw-sample + aggregate), issue them as
   **parallel tool calls in a single turn** (one round-trip out, one
   back) instead of one query per turn. The discovery prefix
   (search→get_dataset) is inherently serial; the queries after it
   are not — batch them.

## Recipe: district price **trend** (the common BA request)

```
plan: intent=trend → strategy=aggregate-SQL; dataset=<lvr-trades>; queries=1

1. opendata-search_datasets(query="實價登錄", domain="realestate_land", limit=10)
2. opendata-get_dataset(dataset_id=...)   # read schema.columns ONCE
3. opendata-query_rows(
     dataset_id=...,
     where="\"鄉鎮市區\" ILIKE '%中山%' "
           "AND \"交易年月日\" >= '1130519' "
           "GROUP BY substr(\"交易年月日\",1,5) "
           "ORDER BY substr(\"交易年月日\",1,5)",
     columns="substr(\"交易年月日\",1,5) AS ym, "
             "count(*) AS deals, "
             "median(CAST(\"總價元\" AS DOUBLE)) AS median_price",
     limit=5000,   # ceiling only — ~24 monthly rows actually return
   )
4. save_curated_csv + save_meta   # the monthly aggregate IS the deliverable
```

## Recipe: raw sample (only when caller wants individual transactions)

```
plan: intent=sample → strategy=limit 50; dataset=<id>; queries=1
opendata-query_rows(dataset_id=..., where="\"鄉鎮市區\" ILIKE '%中山%' "
  "ORDER BY \"交易年月日\" DESC", limit=50)
```

## Recipe: building permit volume by year

```
1. search_datasets(query="使用執照", domain="realestate_land")
2. get_dataset → confirm column names (often: 縣市別, 核發年月, 戶數, 樓層數)
3. query_rows with WHERE on 核發年月 prefix, ORDER BY 核發年月 DESC
4. save + meta
```

## Domain-specific gotchas

- **Date format**: 內政部 datasets use **民國 YYYMMDD** (e.g. `1130315` = 2024-03-15). Filter with string prefix matching: `"\"交易年月日\" LIKE '113%'"` for ROC year 113.
- **Price units**: `總價元` is in TWD (not 萬元). Don't mistake the unit.
- **Address columns**: often two fields — `土地區段位置` (parcel) and `路名` / `門牌` (address). The full address may need concatenation downstream.
- **Anonymization**: addresses below house-number granularity are usually masked (`x` characters). Don't try to "fix" them.

## Filename convention

`realestate_land__<dataset_id>__<TODAY>[__<region-slug>].csv`

`<TODAY>` is the `compact` field of `get_today_utc()` (call it once at the start of the task — see the `dataset-curation` skill, step 0).

Example: `realestate_land__38104__20260506__taipei-daan.csv`

## Composing with BA Agent

The BA Agent reads from `/app/data/shared/costaff-agent-twinkle-hub/`. Tell the
caller (in the **Done** line of the report) which file they should hand to BA
for analysis, e.g.:

> Done: pulled 487 rows of 大安區 Q1-2024 實價登錄. Hand
> `realestate_land__38104__20260506__taipei-daan-q1.csv` to BA Agent for
> price-distribution analysis.
