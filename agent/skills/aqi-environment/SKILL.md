---
name: aqi-environment
description: >
  Pull Taiwan air-quality (AQI / PM2.5 / 空氣品質) and environmental
  monitoring data. Use when the request mentions: AQI, 空氣品質, PM2.5,
  PM10, 細懸浮微粒, 臭氧, 河川水質, 水庫, 雨量, 降雨, 廢棄物回收, 噪音,
  碳排, 環境監測, environmental, pollution. Maps to Twinkle Hub
  `environment` domain. Often used for snapshot monitoring, time-series
  trends, and station-level comparisons.
---

# AQI & Environment Skill

Specialized workflow for the `environment` domain.

## When to use

Tasks involving any of:
- 空氣品質 / AQI / PM2.5 / PM10 / O3 / NOx / SO2
- 河川水質 / 水庫 / 雨量 / 降雨 / 水文
- 廢棄物 / 資源回收
- 噪音
- 碳排放 / 溫室氣體
- 生態 / 林班 / 保育
- 氣象（天氣、溫濕度）

## Anchor datasets we've already validated

| dataset_id | name | freq | notes |
|---|---|---|---|
| `28202` | 空氣品質監測月值 | 每月 | All-string columns: `siteid`, `sitename`, `itemid`, `itemname`, `itemengname`, `itemunit`, `monitormonth`, `concentration`. `itemname` enumerates parameters (PM2.5, 風速, 溫度, 相對濕度, 甲烷 …). |

For others, always discover via `search_datasets(domain="environment")`.

## Recipe: most recent AQI / pollutant readings for a station

```
0. Call get_today_utc() once. Hold the `compact` value for filename use.

1. opendata-search_datasets(query="空氣品質", domain="environment", limit=10)
   → look for monthly or hourly air quality dataset.

2. opendata-get_dataset(dataset_id=...)
   → confirm column names. Stations are usually identified by both
     siteid (numeric code) and sitename (Chinese name).

3. opendata-query_rows(
     dataset_id="28202",
     where="\"sitename\" = '林森' AND \"itemname\" = 'PM2.5' "
           "ORDER BY \"monitormonth\" DESC",
     limit=12,
   )
   → 12 months of PM2.5 history for 林森 station.

4. save_curated_csv + save_meta.
```

## Recipe: full snapshot for one station, one month

```
1. opendata-query_rows(
     dataset_id="28202",
     where="\"sitename\" = '林森' AND \"monitormonth\" = '202603' "
           "ORDER BY \"itemname\"",
     limit=100,
   )
   → all monitored parameters for 林森 in 2026-03.

2. save + meta.
```

## Domain-specific gotchas

- **All values are strings.** `concentration: "20.9"` is text, not a number — downstream BA Agent must `pd.to_numeric(...)` itself.
- **Column names ARE English.** Don't try `\"監測月份\"` — that's a display label, the actual SQL column is `monitormonth`. (We hit this exact Binder Error during agent commissioning.)
- **`itemname` vs `itemengname`** — Chinese label vs English code. `itemname='細懸浮微粒'` ↔ `itemengname='PM2.5'`. Either works for `WHERE`, English is shorter / safer.
- **`monitormonth` format**: `YYYYMM` as string (e.g. `'202603'`). Use string comparison for ranges: `"\"monitormonth\" >= '202601' AND \"monitormonth\" <= '202612'"`.
- **Units differ per item**. Always include `itemunit` in projected columns when reporting numbers.

## Filename convention

`environment__<dataset_id>__<TODAY>[__<station>][__<param>].csv`

`<TODAY>` is the `compact` field of `get_today_utc()` (call it once at the start of the task).

Examples (assuming today is 20260506):
- `environment__28202__20260506__linsen-pm25.csv` (station + param history)
- `environment__28202__20260506__linsen-202603.csv` (station snapshot)

## Output Hint to the Caller

When the caller is an analytic agent (BA), highlight that values are
strings. Example **Done** line:

> Done: 12 months PM2.5 history for 林森. Note: `concentration`
> is string-typed; cast to float before plotting. File:
> `environment__28202__20260506__linsen-pm25.csv`.
