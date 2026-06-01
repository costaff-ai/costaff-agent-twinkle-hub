---
name: tw-opendata-tourism
description: Query Taiwan tourism OpenData via Twinkle Hub MCP. 涵蓋交通部觀光署 (TBROC) 國家風景區/觀光景點/旅館/民宿/觀光客流量;原住民部落觀光;各縣市政府觀光局 in-city 景點;國家公園管理處 (墾丁/玉山/陽明山/太魯閣/雪霸/金門/東北角/澎湖 等);內政部營建署 (前) → 國家公園署 (2023) 自然保護區;交通部觀光局自行車道.含 lat/lon 景點 ~50,000+ 筆,適合做 itinerary 規劃 / 商圈分析 / 觀光客流量預測.繁體中文 corpus.
license: Source data 政府資料開放授權條款-1版 (交通部觀光署 + 各縣市政府觀光局 + 國家公園署). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_datasets` + `query_rows` tools.
metadata:
  corpus: tourism
  source: 交通部觀光署 + 國家公園署 + 各縣市政府觀光局
  language: zh-tw
  domain: leisure_tourism
  version: "1.0.0"
---

# tw-opendata-tourism — 觀光旅遊資料

## Corpus 概況

| 主管機關 | dataset 數量 (~) | 典型內容 |
|---|---|---|
| 交通部觀光署 (TBROC, 2023 改制) | 400+ | 觀光景點、旅館、民宿、觀光客流量、國家風景區 |
| 內政部國家公園署 (2023.09 改制, 前營建署國家公園組) | 100+ | 9 座國家公園 (墾丁/玉山/陽明山/太魯閣/雪霸/金門/東北角/澎湖/壽山) |
| 各縣市政府觀光局 | 500+ | 地方景點、節慶、行銷 |
| 原住民族委員會觀光相關 | 50+ | 原民部落體驗 / 部落工坊 |
| 觀光遊樂業協會 (民間) | (商業, 不在 OpenData) | — |
| 涵蓋更新頻率 | — | 即時 (觀光客流量) / 每月 (旅館入住率) / 不定期 (景點 metadata) |

## 何時用本 skill

「觀光 / 旅遊 / 景點 / 國家公園 / 國家風景區 / 旅館 / 飯店 / 民宿 / 觀光客 / 國際旅客 / 來台 / 觀光局 / 觀光署 / 玉山 / 太魯閣 / 墾丁 / 陽明山 / 自行車道 / 部落體驗 / 行銷活動」相關時優先載入. **不適用於**: 商業訂房系統 (Booking/Agoda)、個別旅館營收 (商業).

## MCP Tools

### `search_datasets(query, agency?, domain?, limit?)` + `query_rows(...)`

## 範例 query (繁體中文)

| 使用者問題 | 對應做法 |
|---|---|
| 「九份 + 金瓜石景點清單 (含 lat/lon)」 | `search_datasets("景點", agency="觀光署")` → query_rows filter "九份" OR "金瓜石" |
| 「2024 玉山國家公園入山人次」 | `search_datasets("玉山 入山", agency="國家公園署")` |
| 「2024 來台旅客國籍前 10」 | `search_datasets("來台旅客 國籍", agency="觀光署")` |
| 「全國民宿登錄 by 縣市」 | `search_datasets("民宿 登錄", agency="觀光署")` |
| 「東北角自行車道」 | `search_datasets("自行車道", agency="觀光署")` |
| 「2024 國家風景區人次排名」 | `search_datasets("國家風景區 遊客", agency="觀光署")` |
| 「台南節慶活動」 | `search_datasets("節慶 活動", agency="臺南市政府")` |

## 機關名稱速查 (catalog 全名)

```
交通部觀光署                            (TBROC, 前: 交通部觀光局, 2023.09 改制)
內政部國家公園署                        (前: 內政部營建署國家公園組, 2023.09 改制)
各國家公園管理處 (玉山 / 太魯閣 / 墾丁 / 陽明山 / 雪霸 / 金門 / 東北角 / 澎湖 / 壽山)
各縣市政府觀光旅遊局/處
各國家風景區管理處 (e.g. 阿里山國家風景區管理處)
原住民族委員會
```

## 國家公園速查 (9 座)

```
玉山國家公園        中部, 玉山主峰 / 八通關
太魯閣國家公園      花蓮, 大理石峽谷
墾丁國家公園        屏東, 海岸 / 珊瑚礁
陽明山國家公園      台北, 大屯火山群
雪霸國家公園        苗栗/新竹/台中, 雪山主峰
金門國家公園        金門, 戰地史蹟
東沙環礁國家公園    海洋 (僅軍方/學者可入)
台江國家公園        台南, 黑面琵鷺 / 紅樹林
澎湖南方四島國家公園 澎湖, 玄武岩
壽山國家自然公園    高雄, 都會型
```

## 重要 dataset 範例

```
景點 (POI)         全國 ~50k 筆, 含 lat/lon + 中英文名 + 開放時間
旅館列表           全國觀光旅館 (五星/三星等) + 一般旅館 + 民宿
觀光客流量         月度國際 / 國內旅遊
國家風景區入次     13 大國家風景區 (北海岸/東部海岸/阿里山/日月潭...) 
節慶活動           月度全國節慶 (放天燈 / 媽祖遶境 / 鹽水蜂炮)
觀光遊樂業         遊樂園 / 動物園
```

## 最佳實踐

1. **agency 改制**: 觀光局 (舊) vs 觀光署 (2023.09+); 兩個都試
2. **「景點」vs「觀光地」vs「觀光地區」**: 詞彙混用, 用 broader query 抓再細看
3. **lat/lon 多為 WGS84**: 直接 Google Maps 用, 部分早期 dataset 是 TWD97 (見 geo skill)
4. **旅館分級**: 五星/四星/三星/一般/民宿/不分等, 看 dataset 注釋
5. **觀光客流量**: 國際 (來台外國旅客) vs 國內 (台灣人遊本國), 注意區分
6. **節慶日期變動**: 春節/中秋等農曆節, dataset 標農曆 vs 西曆 分清

## 注意事項

- 部分國家公園入山需「申請」(e.g. 玉山頂峰), 流量 dataset 已 含申請數據
- 民宿合法登記 vs 黑民宿: dataset 只收登記合法, 黑民宿不在 OpenData
- 旅館入住率 (RevPAR / OCC) 上市公司有, 私人不公開

## 與其他 skill 的邊界

- **觀光相關地理空間 (POI lat/lon, 國家公園界線)** → `tw-opendata-geo` (overlap; geo skill 更通用, 本 skill 更主題)
- **觀光局政府採購 (行銷標案)** → `tw-opendata-pcc`
- **觀光相關交通 (公車 / 高鐵到景點)** → `tw-opendata-transportation`
- **節慶 / 文化資產 (e.g. 鹽水蜂炮)** → `tw-opendata-culture` (民俗指定)
- **原民部落觀光** → 本 skill + `tw-opendata-population` (原民會主管)
