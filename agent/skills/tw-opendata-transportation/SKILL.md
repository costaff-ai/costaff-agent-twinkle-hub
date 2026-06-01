---
name: tw-opendata-transportation
description: Query Taiwan transportation batch datasets via Twinkle Hub MCP. 涵蓋台鐵 / 高鐵 / 北捷 / 桃捷 / 高捷 / 台中捷運 / 公路客運 / 高公局 / 民航 等路線、站點、票價、時刻表、年度運量統計, 來源交通部及各營運單位 OpenData。**僅 batch dataset, 不含 real-time 到站/誤點/車流** (real-time 需用 hub-side TDX tools 另行查詢, 見 SKILL body 後段)。Use for 路線 / 站點查詢 / 票價計算 / 時刻表 / 運量歷史統計 / 交通建設規劃資料。繁體中文 corpus, 交通部 + 各營運機關公開資料。
license: Source data 政府資料開放授權條款-1版 (交通部及各營運單位). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_datasets` + `query_rows`. For real-time data see hub-side TDX tools (separate).
metadata:
  corpus: transportation
  source: 交通部 + 台鐵 + 高鐵 + 各捷運公司 + 高公局 + 民航局
  language: zh-tw
  realtime_complement: TDX (tdx.transportdata.tw) — 透過 hub-side tools, 不在本 skill
  version: "1.0.0"
---

# tw-opendata-transportation — 台灣交通批次資料

## Corpus 概況

| 領域 | 來源機關 / dataset 範例 | 內容 |
|---|---|---|
| 台鐵 | 交通部臺灣鐵路管理局 | 車站基本資料、路線、票價、年度運量、誤點統計 (歷史) |
| 高鐵 | 台灣高鐵公司 | 12 站基本資料、票價、班次表、年度運量 |
| 北捷 | 台北捷運公司 | 站點 lat/lon、路線、票價、年度進出站次數 |
| 桃捷 | 桃園捷運公司 | 站點、路線、年度運量 |
| 高捷 | 高雄捷運公司 | 站點、路線、紅橘環狀年度運量 |
| 台中捷運 | 中捷公司 | 綠線站點、運量 |
| 公路客運 | 交通部公路總局 | 各客運業者路線、站牌、票價 |
| 高公局 | 交通部高速公路局 | 路網、收費站、ETC 流量歷史、施工資訊 |
| 民航 | 交通部民航局 | 機場、航線、年度客貨運量 |
| 港埠 | 交通部航港局 | 各港口、年度貨運量 |
| 自行車 / Ubike | 各縣市政府 | 站點 lat/lon、車輛數 (歷史 snapshot) |
| 時間範圍 | 各 dataset 不同, 多為 2018+ | 部分回溯到 2010 |
| 同步 | 各 dataset 自身 cadence, 我們透過 cadence safety net 接力 | |

## 何時用本 skill

「台鐵 / 高鐵 / 捷運 / 公路客運 / 高速公路 / 民航 / 機場 / 票價 / 時刻表 / 站點 / 路線 / 運量統計 / 交通建設」**批次 / 歷史** 資料時優先載入。

**❌ 不適用於即時資訊**（real-time），下列要走另外 hub-side tools (見後段):
- 即時到站時間 (e.g. 「下一班高鐵幾分鐘到」)
- 即時誤點狀況
- 即時車流 / 國道塞車
- 即時 Ubike 可借車數
- 即時航班到達

## MCP Tools

### `search_datasets(query, ...)` — 找 transportation dataset

```python
search_datasets(query="台鐵 車站", domain="transportation", limit=10)
```

或 by agency:
```python
search_datasets(query="", agency="台北大眾捷運股份有限公司", limit=20)
```

### `get_dataset(dataset_id, sample_rows=3)` + `query_rows(...)`

標準流程：先 `search_datasets` 找 dataset_id, `get_dataset` 看 schema, `query_rows` 查資料。

## 範例 query (batch only)

| 使用者問題 | 對應做法 |
|---|---|
| 「找台鐵 1000 號車站的位置」 | `search_datasets("車站", agency="交通部臺灣鐵路")` → 找 dataset → `query_rows` filter station_id |
| 「高鐵台中站到台北的票價」 | `search_datasets("高鐵 票價", agency="台灣高鐵")` → `query_rows` |
| 「北捷信義線歷年運量」 | `search_datasets("北捷 信義線 運量", agency="台北大眾捷運")` |
| 「台北市 Ubike 站點清單」 | `search_datasets("Ubike", agency="台北市政府交通局")` |
| 「2023 國道客運大客車事故」 | `search_datasets("國道 事故 客運", domain="transportation")` |
| 「桃園機場 2024 客運量」 | `search_datasets("桃園機場 客運量", agency="交通部民用航空局")` |

## 最佳實踐

1. **agency 精準寫**: 「台鐵」抓不到, 用「交通部臺灣鐵路管理局」或「臺灣鐵路公司」(2024 改制)
2. **路線中文有正式名稱**: 「板南線」官方叫「板橋-南港」線; 「紅線」是俗稱, 北捷 dataset 用「淡水信義線」
3. **station_id 格式**:
   - 台鐵: 4 位數字 (e.g. 1000=七堵)
   - 高鐵: 1-3 字英文 (e.g. NAN=南港, TAI=台南)
   - 北捷: 字母+數字 (e.g. R10=士林)
   - 各系統不互通
4. **年度運量是統計後資料**: 通常隔年 Q1 才齊
5. **lat/lon 大多有**: 站點 dataset 通常含座標, 可用 `tw-opendata-geo` 跨 skill 做距離篩選

## 注意事項

- 各營運單位 dataset 結構不一, 同樣是「車站列表」欄位名可能差很大
- **2024 台鐵改制**: 「交通部臺灣鐵路管理局」轉「臺灣鐵路股份有限公司」, agency 名稱有混雜
- **疫情影響 (2020-2022)**: 客運量歷史趨勢不能線性外推
- **票價** 可能含優惠後實價, 看 dataset metadata 註明

## 即時資料 → hub-side TDX tools

> ⚠️ **本 skill 不涵蓋即時資料**。Twinkle Hub 另有 **TDX (Transport Data eXchange) 相關 tools**
> 提供以下即時 query (詳細 tool list 請載入 hub tool catalog 或詢問:「查 hub 有哪些 TDX tools」):
>
> - 即時到站時間 (台鐵 / 高鐵 / 各捷運)
> - 即時誤點 / 取消 班次
> - 即時車流 / 平均車速 (國道)
> - 即時 Ubike 可借/可停 數
> - 即時航班到達 / 起飛 狀態
>
> TDX 是交通部主導的 [tdx.transportdata.tw](https://tdx.transportdata.tw) 整合 portal,
> 涵蓋全國 PTX 大眾運輸 + 國道 + 民航 + 港埠 即時數據。需要 OAuth client credentials 認證,
> 由 hub 端統一管理（用戶 agent 不需自己取 token）。
>
> **agent 路由建議**: 使用者問「下一班...幾點到」/「現在塞車嗎」/「Ubike 還有車嗎」這類即時
> 問題時, **不要用本 skill**, 改用 hub 的 TDX tool（具體 tool name 隨 hub 版本而定）。

## 與其他 skill 的邊界

- **即時資料** → hub-side TDX tools (上段說明)
- **站點地理座標 / 商圈分析** → `tw-opendata-geo` (cross-skill 用 lat/lon)
- **交通建設政府採購招標** → `tw-opendata-pcc` (搜 agency LIKE '%交通%' 或 '%高公局%')
- **交通事故肇事/賠償判決** → `tw-opendata-judicial` (case_type='民事' / '刑事', 搜「車禍」「酒駕」)
- **交通法令** → `tw-opendata-general` (法務部全國法規 dataset)
