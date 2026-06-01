---
name: tw-opendata-realestate
description: "Query Taiwan 不動產實價登錄 (LVR Lien Valuation Registry) via Twinkle Hub MCP. 內政部地政司全國 2012 年起公開的不動產買賣/租賃/預售三類成交資料, 涵蓋 6 都+16 縣, 含建物坪數/單價/地段/樓層/型態。3 個 synthetic datasets: `lvr-trades` (買賣)、`lvr-rentals` (租賃)、`lvr-presale` (預售)。Use for 房價分析 / 預售屋成交 / 租金行情 / 學區比價 / 都更前後價格變化 / 投資物件 due diligence。繁體中文 corpus, 內政部地政司公開資料。"
license: Source data 政府資料開放授權條款-1版 (內政部地政司). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_datasets` + `query_rows` tools (LVR via SQL over synthetic dataset_ids).
metadata:
  corpus: realestate
  source: 內政部地政司 LVR 全國實價登錄
  language: zh-tw
  datasets:
    - lvr-trades
    - lvr-rentals
    - lvr-presale
  version: "1.0.0"
---

# tw-opendata-realestate — 實價登錄查詢

## Corpus 概況

| Dataset | 內容 | 時間範圍 |
|---|---|---|
| `lvr-trades` | 不動產買賣成交 | 2012-08 → 至今, 每季更新 |
| `lvr-rentals` | 不動產租賃成交 | 2015-07 → 至今, 每季更新 |
| `lvr-presale` | 預售屋成交 | 2021-07 → 至今 (預售屋強制揭露法), 每季更新 |
| 涵蓋區域 | 全 6 都 + 16 縣市, 全鄉鎮 |
| 來源 | 內政部地政司 [實價登錄專區](https://lvr.land.moi.gov.tw) |

## 何時用本 skill

「實價登錄 / 房價 / 預售屋 / 租金 / 房地產 / 不動產 / 看屋 / 物件 / 坪數 / 單價 / 行情 / 都更 / 地段比較」相關時優先載入。**不適用於**：建商廣告價、未公開的私下成交、銀行估價、海外房產。

## MCP Tools

### `query_rows(dataset_id, where, columns, limit)` — SQL 查詢

```python
query_rows(
    dataset_id="lvr-trades",
    where="city = '台北市' AND district = '大安區' AND total_price_ntd > 50000000",
    columns=["transaction_date", "address", "total_price_ntd", "ping_unit_price"],
    limit=50,
)
```

DuckDB SQL 直接跑 normalised CSV, 第一次 call 會 lazy-materialize cache。

### `get_dataset(dataset_id, sample_rows=3)` — 看 schema + 範例

```python
get_dataset("lvr-trades", sample_rows=3)
```

回 dataset metadata + 欄位列表 + 3 筆 sample 看資料長相。

### `search_datasets("實價登錄", domain="economy_business")` — 找其他相關 dataset

少用, 已知三個 dataset_id 直接 `query_rows` 即可。

## 三個 dataset 主要欄位（公版命名）

### `lvr-trades` (買賣)

```
transaction_date          交易日期 (YYYY-MM-DD)
city, district            城市 / 鄉鎮市區
address                   地址 (去除門牌部分數字)
building_type             建物型態: 住宅 / 透天厝 / 公寓 / 住商混合 / ...
total_floor               總樓層
transaction_floor         交易樓層
building_age_years        屋齡 (年)
building_ping             建物坪數
land_ping                 土地坪數
parking_ping              車位坪數
total_price_ntd           總價金 (新台幣元)
ping_unit_price           每坪單價 (新台幣元/坪)
parking_price_ntd         車位總價
note                      備註 (含特殊交易事件)
```

### `lvr-rentals` (租賃)

```
+ rent_ntd_per_month      月租金
+ deposit_ntd             押金
+ rental_duration_months  租期月數
+ has_furniture           是否含家具
```

### `lvr-presale` (預售)

```
+ presale_project_name    建案名稱
+ developer               建商
+ planned_completion_date 預計完工日
+ contract_date           簽約日
```

## 範例 query

| 使用者問題 | 對應 call |
|---|---|
| 「台北大安區去年 5000 萬以上成交」 | `query_rows("lvr-trades", where="city='台北市' AND district='大安區' AND total_price_ntd > 50000000 AND transaction_date >= '2024-01-01'", limit=50)` |
| 「新竹東區預售屋平均單價」 | `query_rows("lvr-presale", where="city='新竹市' AND district='東區'", columns=["ping_unit_price","building_ping"])` 後 client aggregate |
| 「板橋租金 3 萬以下 2 房」 | `query_rows("lvr-rentals", where="city='新北市' AND district='板橋區' AND rent_ntd_per_month <= 30000")` |
| 「林口建案 X 預售價格」 | `query_rows("lvr-presale", where="presale_project_name LIKE '%X%' AND district='林口區'")` |
| 「我想看 lvr-trades 資料結構」 | `get_dataset("lvr-trades", sample_rows=5)` |

## 最佳實踐

1. **`address` 已部分遮罩**：門牌號是 `X` 或範圍, 不要試圖反推實際門牌
2. **單價 vs 總價**：投資看 ping_unit_price 比較, 自住看 total_price_ntd
3. **`building_age_years` 可能 NULL**：早期登錄沒填, 用 `WHERE building_age_years IS NOT NULL` 排除
4. **`note` 有特殊事件**：「親友交易」「含車位」「毛胚屋」會嚴重影響單價, 一定要看
5. **季更新有 lag**：當季資料約延後 1.5 個月才完整 (i.e. 2024-Q1 在 2024-05 中才齊)
6. **預售屋 ≠ 新成屋**：預售屋是建案銷售時登錄, 新成屋已交屋後再賣是進 `lvr-trades`

## 注意事項

- 內政部僅公開「成交日」, **每件揭露時點延後 30 天** (依不動產經紀業管理條例)
- 「實價」是申報價, 雖有罰則但部分仍有 inflate/deflate, 適合 trend 分析不適合 single-deal valuation
- 車位、雨遮、屋簷面積 是否計入坪數 各案不同, 比較時要看 `parking_ping` 拆開
- LVR 不含 **法拍屋**、**繼承移轉**、**贈與**

## 與其他 skill 的邊界

- **地籍 / 都市計畫圖** → `tw-opendata-geo` (內政部地政司 SHP)
- **房屋稅 / 地價稅** → `tw-opendata-general` (財政部稅務數據)
- **房屋仲介公會數據** → 不在 OpenData (商業組織)
- **建商財報** → `tw-opendata-general` (證交所 dataset)
