---
name: tw-opendata-tools
description: Meta-skill 教 agent 怎麼用 Twinkle Hub MCP 全部 tools (search_datasets / get_dataset / query_rows / materialize_dataset / list_domains + 各 corpus 專屬 tools)。涵蓋 discovery pattern (search → get → query → materialize 漸進)、何時用哪個 tool、結果 schema 解讀、效能 tips、常見 error pattern。Use as primer 給第一次接觸 Twinkle Hub MCP 的 agent, 或不確定該載入哪個 specialized skill 時的 fallback navigator。繁體中文導引, 但 tool signatures 用 Python typing 標準。
license: Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with full tool set registered.
metadata:
  type: meta-skill
  language: zh-tw
  covers:
    - search_datasets
    - get_dataset
    - query_rows
    - materialize_dataset
    - list_domains
    - search_judicial
    - get_judicial_full
    - search_patents
    - get_patent_body
    - search_exam
    - search_exam_questions
    - get_exam_paper
  version: "1.0.0"
---

# tw-opendata-tools — Twinkle Hub MCP 工具導覽

## 全 tool 速查表

### Generic catalog tools (適用 53k 全部 dataset)

| Tool | 何時用 |
|---|---|
| `list_domains()` | 「我不知道有什麼領域」, 看 17 domain taxonomy + anchor datasets |
| `search_datasets(query, domain?, agency?, quality?, ...)` | discovery: 找哪個 dataset 跟我要的有關 (substring on name+description) |
| `get_dataset(dataset_id, sample_rows=3)` | 拿到 dataset_id 後, 看 metadata + 前 N 筆 sample schema |
| `query_rows(dataset_id, where?, columns?, limit)` | DuckDB SQL 直接查 normalised csv (lazy materialize if first call) |
| `materialize_dataset(dataset_id)` | force fetch + convert + cache (不回 row, 給後續 query_rows 加速) |

### Specialized corpus tools

| Tool | Corpus | 何時用 |
|---|---|---|
| `search_judicial(query, court_code?, case_type?, year?, ...)` | 判決書 360 月 / 6M 件 | 法律研究、判決查詢 → 改載入 `tw-opendata-judicial` |
| `get_judicial_full(jid)` | 同上 | 取單筆判決全文 + T3 metadata |
| `search_patents(query, applicant?, ipc_class?, ...)` | TIPO 280k+ | 專利檢索 → 改載入 `tw-opendata-patent` |
| `get_patent_body(patent_no)` | 同上 | 取完整 claims + abstract |
| `search_exam(query, exam_type?, subject?, ...)` | MOEX 64k 試卷 | 國考 → 改載入 `tw-opendata-exam` |
| `search_exam_questions(query, stem_contains?, ...)` | MOEX 320k 題 | 題目層細查 |
| `get_exam_paper(paper_id)` | 同上 | 取整張試卷全題目 |

## Discovery 黃金 pattern

針對「不知道有什麼 dataset」的 query, 三步走：

```python
# Step 1: 用 domain 縮小範圍
list_domains()
# → 17 個 domain + 每個的 typical_questions / anchor_datasets

# Step 2: search 找 candidate datasets
results = search_datasets(query="加油站", domain="environment", limit=10)
# → list of {dataset_id, name, agency, quality_tier, ...}

# Step 3: 看 schema 後查資料
get_dataset(results[0]["dataset_id"], sample_rows=3)
# → 看欄位有什麼

query_rows(results[0]["dataset_id"], where="city='台北市'", limit=20)
# → 拿真實資料
```

## 何時跳到 specialized skill

如果 user query 落在以下領域, **強烈建議 hint user 改載入對應 skill** (省 token + 更精準):

| User 提到 | 載入 skill |
|---|---|
| 判決、裁判、法院、訴訟、量刑、賠償金額 | `tw-opendata-judicial` |
| 國考、高普考、律師、司法官、會計師、醫師、教師 | `tw-opendata-exam` |
| 專利、發明、新型、設計專利、IPC、TIPO | `tw-opendata-patent` |
| 房價、預售屋、租金、實價登錄、不動產 | `tw-opendata-realestate` |
| 經緯度、行政區、學區、選區、SHP、GeoJSON | `tw-opendata-geo` |
| 政府採購、招標、決標、得標廠商 | `tw-opendata-pcc` |
| 立法院、立委、質詢、議案、IVOD、公報 | `tw-opendata-ly` |
| 其他通用 OpenData query | 留在本 skill, 用 generic catalog tools |

## query_rows 效能 tips

1. **where 越具體越快**: `WHERE date='2024-01-15' AND city='台北市'` 比 `WHERE city LIKE '%'` 快數百倍
2. **columns 只 select 需要的**: 大 dataset 全欄位 select 浪費頻寬
3. **first call lazy materialize**: 第一次 query 一個 dataset 會自動 fetch + convert, 可能等 5-30 秒; 後續 cached
4. **大 dataset 預 materialize**: 如果知道要重複查, 先 `materialize_dataset(id)` 一次
5. **DuckDB ILIKE 比 LIKE 快**: case-insensitive substring 用 ILIKE
6. **避免 LIMIT 1000 後 client 過濾**: 在 SQL where 內過濾, 不要拉回來才過濾

## 常見 error 解讀

| Error | 原因 | 解法 |
|---|---|---|
| `dataset_id not found` | catalog 沒這個 ID, 或剛 retired | `search_datasets()` 重新找 |
| `dataset not materialised` | 純 PDF/SHP/KML, 自動 pipeline 跳過 | 看 metadata.formats 是否有 CSV/JSON; 若無只能下 raw |
| `embed dim mismatch` | specialized search tool 出狀況 | 通常是 server 端問題, retry |
| `LLM endpoint unavailable` | search_judicial 等需要 embed 的 tool 暫時打不到 LLM | 改用 keyword filter (jtitle_contains 等) 不依賴 semantic |
| `chunks corpus empty` | judicial search 但該月還沒 embed | filter year_from / year_to 到 2024+ 已 embed 範圍 |

## metadata 解讀

`get_dataset()` 回的 metadata 重要欄位:

```
update_freq            宣稱頻率: 每1日 / 每1月 / 不定期更新 (≠ 實際更新, 見 observed_freq)
quality_tier           白金 (最佳, 32k 個) / 金 / 銀 / 銅 / 未檢測
formats                ['CSV', 'JSON'] 等 - 影響 query_rows 是否可用
license                授權: 多為「政府資料開放授權條款-1版」(OGDL, CC0 兼容)
agency                 提供機關
metadata_updated       catalog 描述異動時間 (≠ 資料本身異動)
listed_date            首次上架日
encoding_hint          'UTF-8' / 'Big5' / 'CP950'
download_urls          原始 source URL list
domains                我們的 17-domain taxonomy 標籤 (多 label)
is_normalised          True = 已轉成 csv 可 query_rows
```

## 不要做的事

1. **不要 search_datasets 然後直接 query_rows 不看 schema**: 浪費 round trip
2. **不要拿 numeric `dataset_id` 當 int**: 內部 normalise 為 str, 用 `"123"` 不是 `123`
3. **不要用 generic search_datasets 找特定 corpus**: judicial / patent / exam 有專用 search tool, 結果更精準快
4. **不要 sleep + retry materialize**: lazy materialize 是同步的, 第一次 query_rows 完成自動 cache, 後續直接快
5. **不要假設 update_freq 真實**: 用 `list_domains()` 看 typical_questions 或拿了再 sample 一下時間

## 與 specialized skills 的關係

本 skill 是**第一站 / discovery primer**, 不應該長住 context。流程:
1. User query 進來
2. Agent 載入本 skill 識別領域
3. 對應到 specialized skill (e.g. `tw-opendata-judicial`), 改載入該 skill
4. 用 specialized skill 內定義的 tool 做精準 query
5. 必要時跳回本 skill 用 generic catalog tool 補
