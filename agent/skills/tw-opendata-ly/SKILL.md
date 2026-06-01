---
name: tw-opendata-ly
description: Query 立法院 (Taiwan Legislative Yuan) 議案/委員/質詢/院會/IVOD/公報 via Twinkle Hub MCP. 我們 mirror v2.ly.govapi.tw 累積 284,000+ rows 跨 8 個 collections (bills 議案/legislators 立委/gazettes 公報/gazette_agendas 議程/interpellations 質詢/ivods 視訊/meets 會議/committees 委員會)。每日 cron 增量更新。Use for 公民監督 / 法案追蹤 / 立委投票紀錄 / 委員質詢主題分析 / 院會議事日程 / 公報全文檢索 / 政策推動歷程。繁體中文 corpus, ly.govapi.tw 鏡像 (非官方 OGDL, 但合法公開)。
license: Source data mirror from v2.ly.govapi.tw (非官方但合法公開). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `query_rows` against ly-* synthetic datasets.
metadata:
  corpus: ly
  source: v2.ly.govapi.tw + HuggingFace JSONL mirrors
  language: zh-tw
  datasets:
    - ly-bills
    - ly-legislators
    - ly-gazettes
    - ly-gazette_agendas
    - ly-interpellations
    - ly-ivods
    - ly-meets
    - ly-committees
  version: "1.0.0"
---

# tw-opendata-ly — 立法院 8 collections 查詢

## Corpus 概況

| Dataset | 內容 | 規模 |
|---|---|---|
| `ly-bills` | 法案 / 議案 (提案 → 一讀 → 二讀 → 三讀 → 公布) | 80,000+ |
| `ly-legislators` | 歷屆立委 個人資料 | 1,656 |
| `ly-gazettes` | 立法院公報 期刊 | 2,269 |
| `ly-gazette_agendas` | 公報議程 (含發言紀錄) | 100,000+ |
| `ly-interpellations` | 質詢 (口頭/書面) | 大宗 |
| `ly-ivods` | 院會視訊串流 metadata + URL | 大宗 |
| `ly-meets` | 會議紀錄 (院會/委員會/聯席) | 7,913 |
| `ly-committees` | 委員會列表 | 18 |
| 涵蓋範圍 | 第 7 屆 (2008-) 至今, 部分早期屆別 | — |
| 同步頻率 | 每日 03:35 cron --tail 5 增量 | — |
| 來源 | [v2.ly.govapi.tw](https://v2.ly.govapi.tw) (社群 mirror) + HF JSONL dumps | — |

## 何時用本 skill

「立法院 / 立委 / 法案 / 議案 / 質詢 / 院會 / 公報 / IVOD / 三讀 / 委員會 / 政黨表決 / 法律修正案 / 立法院公報」相關時優先載入。**不適用於**：地方議會 (市議會 / 縣議會 — 另一 dataset)、行政院會議 (非立法部門)、司法判決 (用 `tw-opendata-judicial`)。

## MCP Tools

### `query_rows("ly-{collection}", where, ...)` — 主要查詢

```python
query_rows(
    dataset_id="ly-bills",
    where="bill_status='三讀' AND last_update >= '2024-01-01'",
    limit=50,
)
```

DuckDB SQL 直接跑各 collection csv (本機 + GCS mirror 同步)。

### 各 collection 主要欄位

#### `ly-bills` (議案)

```
bill_id              議案 ID
bill_no              議案編號
session, term        屆期
bill_type            類型: 法律案 / 決議案 / 預算案 / 行政命令 / 人事案
bill_name            議案名稱
proposer             提案者 (黨團 / 委員 / 行政院)
bill_status          現況: 提案 / 一讀 / 委員會 / 二讀 / 三讀 / 公布 / 退回 / 撤回
referred_committee   交付委員會
last_update          最近異動日
related_bills        關聯議案
```

#### `ly-legislators` (立委)

```
legislator_id        立委 ID
name                 中文姓名
party                政黨
gender               性別
term                 屆別
constituency         選區 (e.g. 「臺北市第1選舉區」 / 「不分區及僑居國外國民」)
education            學歷
career               經歷
photo_url            照片
```

#### `ly-interpellations` (質詢)

```
interpellation_id
session, term
interpellator        質詢人 (立委)
interpellated        被質詢人 (院長 / 部長)
topic                主題
date                 質詢日期
type                 口頭質詢 / 書面質詢
full_text            質詢全文 (若有)
response             官員答覆
```

#### `ly-ivods` (院會視訊)

```
ivod_id
meet_name
meet_date
video_url            (YouTube / 立法院 server)
duration_min
attendees
```

#### `ly-votes` (記名投票)

```
vote_id, bill_id
date
legislator_id, party
vote_choice          贊成 / 反對 / 棄權 / 缺席
```

(其他 collections schema 用 `get_dataset("ly-{name}", sample_rows=3)` 看)

## 範例 query

| 使用者問題 | 對應 call |
|---|---|
| 「2024 三讀通過的法案」 | `query_rows("ly-bills", where="bill_status='三讀' AND last_update >= '2024-01-01'", limit=100)` |
| 「黃國昌的質詢內容」 | `query_rows("ly-interpellations", where="interpellator='黃國昌'", columns=["date","topic","interpellated"])` |
| 「民眾黨第 11 屆立委」 | `query_rows("ly-legislators", where="party='台灣民眾黨' AND term=11")` |
| 「修法相關 健保 在 2023」 | `query_rows("ly-bills", where="bill_name LIKE '%全民健康保險%' AND last_update LIKE '2023%'")` |
| 「教育及文化委員會 2024 會議」 | `query_rows("ly-meets", where="committee LIKE '%教育及文化%' AND meet_date LIKE '2024%'")` |
| 「找 IVOD 含『核能』關鍵字」 | `query_rows("ly-ivods", where="meet_name LIKE '%核能%' OR topic LIKE '%核能%'", columns=["meet_date","meet_name","video_url"])` |

## 最佳實踐

1. **`term` 屆別 vs `session` 會期**: 一屆 4 年, 一屆有 7-8 會期。「第 11 屆」是當前 (2024-2028), 不要混淆
2. **`legislator_id` 跨表 join**: bills proposer / ivods attendees 都用此 id
3. **`vote_choice` 大寫**: 「贊成」「反對」「棄權」「缺席」, 中文不是 Yea/Nay
4. **`bill_status` 是當下狀態**: 同一 bill 可能多次 query 結果不同, last_update 看異動日
5. **IVOD 視訊 URL 可能失效**: 立法院 server 偶爾搬, YouTube link 較穩定
6. **`gazettes` ≠ `gazette_agendas`**: 前者是公報期刊 metadata, 後者是議程細節含逐字稿

## 注意事項

- 第 7 屆 (2008) 之前的資料覆蓋不完整 (數位化問題)
- 不記名投票 (e.g. 議長/副議長選舉) 不在本 corpus
- 黨團協商記錄 部分不公開
- 質詢「書面答覆」有時 lag 數月才齊
- 預算案的審查細節 (各部會編列) 不全在 ly-bills, 需配 `tw-opendata-general` 找主計總處資料

## 與其他 skill 的邊界

- **地方議會**: 我們有部分縣市議會 dataset (新北/台南/台中等), 在 catalog 內, 用 `tw-opendata-general` `search_datasets("議會")` 找
- **行政院會議 / 部會新聞稿**: `tw-opendata-general` 內各部會 dataset
- **法律全文** (條文本體): `tw-opendata-general` 找法務部全國法規資料庫 dataset
- **立法院預算 / 決算**: `tw-opendata-general` (主計總處)
- **立委個人臉書 / 競選政見**: 不在政府 OpenData 範圍
