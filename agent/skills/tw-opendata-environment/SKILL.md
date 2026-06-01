---
name: tw-opendata-environment
description: Query Taiwan environment & weather OpenData via Twinkle Hub MCP. 涵蓋環境部 (MOENV) 空氣品質 AQI/PM2.5/PM10、水質、噪音、土壤汙染、廢棄物處理;中央氣象署 (CWA) 觀測站歷史氣溫/雨量/濕度/風速、地震紀錄、颱風路徑;水利署 (WRA) 水庫蓄水量、河川水位、雨量站、地下水位;海委會 (OAC) 海水監測、海岸線;林務局森林資源/保育類動植物.涵蓋 1990 年代起歷史長期數據, 每小時/日/月更新.Use for 空氣品質歷史分析 / 颱風研究 / 氣候變遷 / 水資源評估 / 環評 / 環境訴訟 / 自然保育.繁體中文 corpus.
license: Source data 政府資料開放授權條款-1版 (環境部 / 中央氣象署 / 水利署 / 林務局 / 海洋委員會). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_datasets` + `query_rows` tools. 即時觀測資料另由 NCHC 民生公共物聯網 API 提供 (見 skill body 末段).
metadata:
  corpus: environment
  source: 環境部 + 中央氣象署 + 水利署 + 林務局 + 海洋委員會 + 各縣市環保局
  language: zh-tw
  domain: environment
  realtime_complement: NCHC 民生公共物聯網 (scidm.nchc.org.tw)
  version: "1.0.0"
---

# tw-opendata-environment — 環境氣象資料

## Corpus 概況

| 主管機關 | dataset 數量 (~) | 典型內容 |
|---|---|---|
| 環境部 (MOENV) | 800+ | 空氣品質 AQI/PM2.5/PM10/O3/NOx、水質 (河川/湖泊/海岸)、噪音、土壤汙染、廢棄物清運統計、環評書件 |
| 中央氣象署 (CWA) | 300+ | 觀測站歷史氣溫/雨量/濕度/氣壓/風速 (1900 起部分站)、地震紀錄、颱風路徑、海象 |
| 水利署 (WRA) | 200+ | 全國水庫蓄水量、河川水位、雨量站、潮位、地下水位、灌溉用水 |
| 林務局 / 林業及自然保育署 | 150+ | 森林資源調查、保育類動植物、國家森林遊樂區、保護區範圍 |
| 海洋委員會 (OAC) | 100+ | 海水水質、海岸地形、海洋廢棄物、漁業資源 |
| 各縣市環保局 | 500+ | 地方空品站、垃圾車路線、稽查案件 |
| 涵蓋更新頻率 | — | 每小時 (AQI、地震) / 每日 (水庫) / 每週 / 每月 / 每年 |

## 何時用本 skill

「空氣品質 / AQI / PM2.5 / 水質 / 水庫 / 河川 / 颱風 / 氣溫 / 雨量 / 地震 / 環評 / 廢棄物 / 噪音 / 森林 / 保育 / 海洋 / 氣象署 / 環境部 / 水利署」相關時優先載入. **不適用於**: 即時 AQI alarm (商業 app / NCHC IoT API 適合)、私人氣象台、外國氣象.

## MCP Tools

### `search_datasets(query, agency?, domain?, limit?)` + `query_rows(...)` 標準流程

```python
search_datasets(query="空氣品質 監測站", agency="行政院環境保護署", limit=10)
# 環境部 2023 改制前後 agency 名稱有差, 兩個都試
get_dataset("12345", sample_rows=3)
query_rows("12345", where="county='台中市' AND date >= '2024-01-01'")
```

## 範例 query (繁體中文)

| 使用者問題 | 對應做法 |
|---|---|
| 「2024 台中市 PM2.5 月平均」 | `search_datasets("PM2.5 月平均", agency="環境部")` → query_rows |
| 「2023 颱風路徑歷史」 | `search_datasets("颱風 路徑", agency="中央氣象署")` |
| 「翡翠水庫蓄水率歷史」 | `search_datasets("水庫 蓄水", agency="水利署")` → filter 水庫名稱 |
| 「台北 2024 雨量站日資料」 | `search_datasets("雨量站", agency="中央氣象署")` |
| 「環評書件 2024 通過案件」 | `search_datasets("環評 書件", agency="環境部")` |
| 「歷年地震 規模 5+」 | `search_datasets("地震 紀錄", agency="中央氣象署")` |
| 「全國河川 BOD 水質」 | `search_datasets("河川 水質 BOD", agency="環境部")` |
| 「林務局保育類動物名錄」 | `search_datasets("保育類 名錄", agency="林務局")` 或「林業及自然保育署」 |

## 機關名稱速查

```
環境部                                   (前: 行政院環境保護署 EPA)
環境部大氣環境司
環境部水質保護司
環境部資源循環署
環境部氣候變遷署
交通部中央氣象署                         (前: 中央氣象局 CWB)
經濟部水利署                             (WRA)
農業部林業及自然保育署                   (前: 林務局)
農業部水土保持及農村發展署               (前: 水土保持局)
海洋委員會                               (OAC)
海洋委員會海洋保育署
各縣市環境保護局
```

## 重要 dataset 範例

```
空氣品質歷史    各縣市 / 各監測站 / hourly + daily + monthly
水庫蓄水率      翡翠 / 石門 / 曾文 / 烏山頭 / 等 18 主要水庫
雨量站          全國 ~600 站 hourly
測站氣溫        ~30 主要觀測站 daily 1900+ (有些站數據從 1897)
地震紀錄        全部 1900+, 規模 / 震央 / 深度 / 強度分布
河川水質        全國 ~70 河系, 月測 BOD/COD/DO/NH3-N
颱風路徑        1958+ 全部影響台灣的颱風
```

## 最佳實踐

1. **agency 改制**: 環境部 (2023.08 改制), CWA (2023.09), 林業及自然保育署 (2023.08), 兩個名稱都要試
2. **historical 氣溫資料超長**: 部分站從 1897 (日治時期) — 適合氣候變遷研究
3. **空品 hourly 數據量大**: 一個站一年 8760 筆, 用 date BETWEEN 過濾
4. **AQI ≠ PM2.5**: AQI 是綜合指標, PM2.5 是其中一項。要 PM2.5 就直接抓濃度
5. **水庫名稱常見別名**: 「德基」「中部水庫」, 別 case-sensitive match
6. **環評書件多為 PDF**: catalog 內有 metadata, 但全文要去環境部 EIA 系統下載

## 注意事項

- **即時 AQI / 雨量** 我們 batch dataset 不適合, 走 NCHC 民生公共物聯網 API 即時抓 (見下段)
- 颱風路徑 dataset **格式不一**: 部分 GeoJSON, 部分 CSV 點序, 部分需 join 多 table
- 監測站位置常微調 (e.g. 站搬遷), 跨年比較要看 station_id 一致

## 即時資料 → NCHC 民生公共物聯網

> 真正即時的空品 / 氣象 / 水文 / 海洋資料, 用交通部 [scidm.nchc.org.tw](https://scidm.nchc.org.tw)
> (NCHC 國網中心民生公共物聯網) — 提供 IoT 即時 API。註冊免費, 不在本 skill 範圍。

## 與其他 skill 的邊界

- **環境訴訟 / 公害判決** → `tw-opendata-judicial`, search「公害」「環評」「水污染」
- **環評書件招標** → `tw-opendata-pcc`, agency LIKE '%環境%'
- **氣象 / 地理空間 圖層** → `tw-opendata-geo` (颱風路徑 GeoJSON / 國家公園 SHP)
- **環境保護法律案** → `tw-opendata-ly`, search「空氣污染防制法」
- **農業相關環境 (土壤 / 水質)** → `tw-opendata-agriculture` 也有相關 dataset
