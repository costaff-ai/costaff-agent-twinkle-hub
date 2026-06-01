---
name: tw-opendata-health
description: Query Taiwan health & medical OpenData via Twinkle Hub MCP. 涵蓋健保署 (NHIA) 特約醫院/藥局/牙醫/診所、藥物給付清單、看診人次統計;疾管署 (CDC) 傳染病通報、COVID-19/流感/腸病毒疫情、疫苗接種;食藥署 (TFDA) 藥品/化妝品/保健食品/食品安全;國民健康署癌症篩檢、慢性病。Use for 醫療院所查詢 / 藥品給付 / 疫情統計 / 食安召回 / 健保特約 / 公衛數據 / 疾病監測。繁體中文 corpus, 衛生福利部及所屬機關公開資料.
license: Source data 政府資料開放授權條款-1版 (衛生福利部及所屬機關). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_datasets` + `query_rows` + `list_domains` tools.
metadata:
  corpus: health
  source: 衛生福利部 (健保署 / 疾管署 / 食藥署 / 國健署 / 中醫藥司 / 心理健康司)
  language: zh-tw
  domain: health_food
  version: "1.0.0"
---

# tw-opendata-health — 健康衛福資料

## Corpus 概況

| 主管機關 | dataset 數量 (~) | 典型內容 |
|---|---|---|
| 健保署 (NHIA) | 200+ | 特約醫院/藥局/牙醫/檢驗所列表、藥品給付、診療項目、醫療費用統計 |
| 疾管署 (CDC) | 300+ | 法定傳染病週/月/年報、COVID-19/流感/登革熱/腸病毒/結核病、疫苗接種率 |
| 食藥署 (TFDA) | 400+ | 藥品許可證、化妝品許可證、保健食品、食品違規/召回、藥物動物實驗 |
| 國民健康署 | 100+ | 癌症登記、四癌篩檢、孕產婦保健、菸害防制、口腔健康 |
| 中醫藥司 | 50+ | 中藥材、製劑、藥商 |
| 心理健康司 | 30+ | 精神醫療、心理諮商機構、自殺通報 |
| 涵蓋更新頻率 | — | 每日 (COVID、急診壅塞) / 每週 (傳染病) / 每月 (健保) / 每季 / 每年 |

## 何時用本 skill

「健保 / 藥局 / 醫院 / 診所 / 牙醫 / 疾管 / COVID / 流感 / 疫苗 / 食藥署 / 食品安全 / 化妝品 / 保健食品 / 癌症 / 健檢 / 衛福部」相關時優先載入. **不適用於**: 個別病歷 (個資不公開)、醫師執照細節 (專業團體)、私人保險 (商業).

## MCP Tools (純 catalog query)

### `search_datasets(query, agency?, domain?, limit?)` — 找對應 dataset

```python
search_datasets(query="健保特約藥局", agency="衛生福利部中央健康保險署", limit=10)
```

### `get_dataset(dataset_id, sample_rows=3)` — 看 schema + sample

```python
get_dataset("31000", sample_rows=3)
```

### `query_rows(dataset_id, where?, columns?, limit)` — DuckDB SQL

```python
query_rows(
    dataset_id="31000",
    where="city='台北市' AND district='信義區'",
    columns=["organ_id","name","address","phone"],
    limit=50,
)
```

## 範例 query (繁體中文)

| 使用者問題 | 對應做法 |
|---|---|
| 「台北市信義區的健保特約藥局」 | `search_datasets("健保特約藥局", agency="中央健康保險署")` → 拿 id → `query_rows(... WHERE city='台北市' AND district='信義區')` |
| 「2024 COVID 19 病例週報」 | `search_datasets("COVID 病例", agency="疾病管制署")` |
| 「最近一週流感類流感病例」 | `search_datasets("類流感 監測", agency="疾病管制署")` |
| 「藥品 X 的健保給付」 | `search_datasets("藥品給付", agency="健保署")` → query_rows filter 藥品名稱 |
| 「食藥署最近召回的進口食品」 | `search_datasets("食品 召回 違規", agency="食品藥物管理署")` |
| 「乳癌篩檢率縣市排名」 | `search_datasets("乳癌 篩檢", agency="國民健康署")` |
| 「全國精神醫療機構列表」 | `search_datasets("精神 醫療機構", agency="衛生福利部")` |

## 機關名稱速查（catalog 中常見全名）

```
衛生福利部中央健康保險署             (健保署 NHIA)
衛生福利部疾病管制署                 (疾管署 CDC)
衛生福利部食品藥物管理署             (食藥署 TFDA)
衛生福利部國民健康署                 (國健署 HPA)
衛生福利部社會及家庭署
衛生福利部中央健康保險署
衛生福利部護理及健康照護司
衛生福利部心理健康司
衛生福利部中醫藥司
衛生福利部所屬醫院 (XX 部醫院, e.g. 台北醫院, 桃園醫院)
```

## 最佳實踐

1. **agency 用全名**: 「健保署」抓不到, 用「衛生福利部中央健康保險署」(或先 search_datasets 用模糊 query 試水溫)
2. **疫情數據 lag 1-2 週**: 傳染病週報通常隔週才有最終確診數
3. **個案級別不公開**: 「某某人住院紀錄」抓不到, 政府只開放統計
4. **健保特約**: 4-5 萬家醫療院所, 用 city + district + organ_type 篩選
5. **食藥署許可證**: 一個藥廠多筆 (每藥品一張), 用 manufacturer 過濾彙整
6. **「即時資料」常 stale**: 警政署 A1/A2 即時事故 lag 2-3 週類似, COVID 也 5-7 天 lag

## 注意事項

- 健保資料**完全去識別化**, 不要嘗試 deanonymize 個案
- COVID 統計 2023 後降為週報, 不再每日 push
- 中醫藥資料常用繁體 + 古字 (e.g. 「黃耆」「茯苓」), search 時繁體不要打簡體
- 部分數據是「人次」非「人數」(同一人多次看診算多次), 解釋時要區分

## 與其他 skill 的邊界

- **健康相關訴訟 (醫療糾紛判決)** → `tw-opendata-judicial`, search query「醫療糾紛」或案由「侵權行為損害賠償」
- **健保特約地點 + 經緯度查附近** → `tw-opendata-geo` (cross-skill 用 lat/lon)
- **醫藥業政府採購** → `tw-opendata-pcc` (e.g. 衛福部疫苗採購)
- **疫苗 / 醫藥相關專利** → `tw-opendata-patent` (TIPO IPC A61 醫藥)
- **食品 / 藥品法規本身** → `tw-opendata-general` (法務部全國法規)
