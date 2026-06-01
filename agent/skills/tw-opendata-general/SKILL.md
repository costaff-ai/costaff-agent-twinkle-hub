---
name: tw-opendata-general
description: Universal entry point for Taiwan government open data via Twinkle Hub MCP. 涵蓋 53,000+ 個 dataset (中央 + 城市門戶), 來自 950+ 提供機關, 含財政、稅務、醫療、衛福、教育、交通、農業、勞動、外交、人口、選舉、產業統計、消保、商業登記、能源、環境等所有政府公開資料。catalog index 含 17 個 domain taxonomy + multi-label classification。Use as fallback / discovery skill for queries that don't fit judicial / exam / patent / realestate / geo specialized skills, 或當不確定哪個 corpus 適合時。繁體中文 corpus。
license: Source data 政府資料開放授權條款-1版 (各機關). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_datasets`, `get_dataset`, `query_rows`, `materialize_dataset`, `list_domains` tools.
metadata:
  corpus: catalog
  source: data.gov.tw 全 catalog (中央 + 城市)
  language: zh-tw
  total_datasets: 53000
  version: "1.0.0"
---

# tw-opendata-general — 台灣 OpenData 通用查詢

## Corpus 概況

| 項目 | 值 |
|---|---|
| 總 dataset 數 | ~53,000 (`data.gov.tw` central + city portals) |
| 提供機關 | ~950 個 (中央部會 + 縣市 + 國營事業) |
| 品質 tier | 白金 32k / 金 14k / 銀 3k / 銅 1k |
| 17 domains (taxonomy) | health_food / education / business_economy / public_admin / transportation / agriculture / labor / environment / housing / energy / culture_arts / social_population / consumer_protection / immigration_diplomacy / legislature / judicial / economy_business |
| 觀測更新頻率 | 5,119 daily, 10,226 weekly, 24,146 monthly, 14,066 dormant (90d /changed 推算) |
| 同步策略 | /changed-based daily refresh + cadence safety nets (見 README mermaid) |

## 何時用本 skill

當查詢涉及 **不在以下五個 specialized skill 範圍** 的政府開放資料時用本 skill：
- 不在 `tw-opendata-judicial` (判決書)
- 不在 `tw-opendata-exam` (國家考試)
- 不在 `tw-opendata-patent` (專利)
- 不在 `tw-opendata-realestate` (實價登錄)
- 不在 `tw-opendata-geo` (地理空間)

也適合**不確定哪個 skill 適合**時用本 skill discover 哪個 corpus 對應。

## MCP Tools

### `search_datasets(query, ...)` — discovery

```python
search_datasets(
    query: str,                       # 名稱 / 描述 substring
    domain: str = None,               # 17 domains 任一, e.g. "health_food"
    agency: str = None,               # 提供機關名稱
    quality: str = None,              # 白金 / 金 / 銀 / 銅
    update_freq: str = None,          # 每1日 / 每1月 / 每1年 / 不定期更新
    fmt: str = None,                  # CSV / JSON / XML / SHP / ...
    normalised_only: bool = False,    # 只回已 normalise 為 .csv 的
    limit: int = 20,
)
```

排序：quality_tier 高優先 → `metadata_updated` desc。

### `get_dataset(dataset_id, sample_rows=3)` — 看 dataset metadata + sample

```python
get_dataset("39281", sample_rows=3)
```

回完整 metadata + 前 N 筆資料看 schema。

### `query_rows(dataset_id, where, columns, limit)` — DuckDB SQL 查

```python
query_rows(
    dataset_id="124159",
    where="organ ILIKE '%板橋%'",
    columns=["organ", "address", "phone"],
    limit=20,
)
```

DuckDB 跑 normalised CSV; 第一次 call 自動 lazy materialize → cache。

### `materialize_dataset(dataset_id)` — 強制 cache warmup

```python
materialize_dataset("39281")
```

force fetch + convert + cache, 不回 row, 給後續 query_rows 加速用。

### `list_domains()` — 17 domain taxonomy

回 taxonomy: scope, exclusions, join_keys, typical questions, anchor datasets per domain。

## 17 Domains 速查

| Domain | 範圍 |
|---|---|
| `health_food` | 醫療衛生、藥品、食品安全、疾病管制 |
| `education` | 學校、招生、學生數據、教育部 |
| `business_economy` | 商業登記、產業統計、進出口貿易 |
| `economy_business` | 金融、證券、銀行、保險 (財政部 / 央行) |
| `public_admin` | 政府組織、人事、公共行政 |
| `transportation` | 交通流量、停車、公共運輸、道路 |
| `agriculture` | 農作物、漁業、林業、農會 |
| `labor` | 就業、薪資、勞動條件、勞工保險 |
| `environment` | 空氣品質、水質、廢棄物 |
| `housing` | 國民住宅、社會住宅、都更 |
| `energy` | 油電、再生能源、電費 |
| `culture_arts` | 文化資產、藝文活動、博物館 |
| `social_population` | 人口、戶政、社會福利、選舉統計 |
| `consumer_protection` | 消保、產品標示、食安 |
| `immigration_diplomacy` | 移民、國民、外交 |
| `legislature` | 立法院、議員、議案、表決 |
| `judicial` | 司法系統 (判決見 `tw-opendata-judicial`, 此為其他相關) |

## 範例 query

| 使用者問題 | 對應 call |
|---|---|
| 「找衛福部疾管署 COVID 19 病例 dataset」 | `search_datasets("COVID-19 病例", agency="衛生福利部疾病管制署", domain="health_food")` |
| 「2024 立法委員投票紀錄」 | `search_datasets("立法委員 表決", domain="legislature")` → 用 `ly-votes` |
| 「全國國中數量」 | `search_datasets("國民中學 統計", domain="education")` |
| 「夏威夷豆 進口量」 | `search_datasets("進口", domain="business_economy")` 找海關進出口 dataset |
| 「板橋附近的稅捐稽徵所」 | `query_rows("124159", where="organ ILIKE '%板橋%'", limit=10)` |
| 「不知道有什麼好用的環境 dataset」 | `list_domains()` 看 environment → 看 anchor datasets |

## 最佳實踐

1. **先 search, 再 get**：不要直接 `query_rows(id)` 沒 schema 知識會打錯欄位
2. **白金 + 每1日 通常最有用**：高品質、active maintained, `quality="白金", update_freq="每1日"`
3. **agency 全名要對**：「衛福部」抓不到, 要「衛生福利部」
4. **domain filter 是 OR**：一個 dataset 可有多 domain, 用 `domain="health_food"` 包含主 domain = 此值的所有 dataset
5. **`normalised_only=True` 過濾掉純 PDF/SHP/KML dataset**：那些 `query_rows` 不能用
6. **`metadata_updated` 不等於資料更新**：是 catalog 描述異動時間, 真實資料異動見 `/changed` (見 README cadence groups 設計)
7. **dataset_id 是字串**：numeric 看起來像 int, 但內部 normalise 為 str

## 注意事項

- 純圖像 / SHP / KML / 純 PDF 的 dataset 在本系統不支援 `query_rows` (在 materialize SKIP_FORMATS 內)
- 部分縣市門戶 dataset (data.taipei, data.kcg.gov.tw 等) 已 mirror 在 catalog 中, 但不全
- 「機密 / 個資」相關 dataset (e.g. 個別納稅資料) 政府不會公開, 不要嘗試

## 與其他 skill 的關係

本 skill 是 **fallback / discovery 入口**, 應該:
1. 先檢查使用者問題能否用 5 個 specialized skill (judicial / exam / patent / realestate / geo) 解決
2. 不能 → 用本 skill 的 `search_datasets` 找對的 dataset
3. 找到後可直接用本 skill 的 `query_rows`, 或 hint 用戶該載入哪個 specialized skill
