---
name: tw-opendata-agriculture
description: Query Taiwan agriculture / forestry / fishery OpenData via Twinkle Hub MCP. 涵蓋農業部 (MOA) 農作物產量/批發市場價格/農藥/肥料;農糧署 (AFA) 稻米/雜糧/蔬菜/水果;漁業署 (FA) 漁獲/養殖/拍賣價;林業及自然保育署 (FANC) 森林資源/保育類;水土保持及農村發展署 (SWCB) 土石流潛勢/水保設施;動植物防疫檢疫署 (BAPHIQ) 動物疫病/植物檢疫;各區農業改良場、各茶業/果樹/水稻試驗所.涵蓋每日批發價、月度產量、年度普查.Use for 農產品價格分析 / 漁獲統計 / 林業資源 / 動植物疫病 / 農藥肥料管理 / 食農教育.繁體中文 corpus.
license: Source data 政府資料開放授權條款-1版 (農業部及所屬機關). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_datasets` + `query_rows` tools.
metadata:
  corpus: agriculture
  source: 農業部 (前農委會) + 農糧署 + 漁業署 + 林業署 + 水保署 + 防檢署 + 各改良場
  language: zh-tw
  domain: agriculture
  version: "1.0.0"
---

# tw-opendata-agriculture — 農林漁牧資料

## Corpus 概況

| 主管機關 | dataset 數量 (~) | 典型內容 |
|---|---|---|
| 農業部 (MOA, 2023 改制) | 500+ | 政策、補貼、農地、農機 |
| 農糧署 (AFA) | 300+ | 稻米/雜糧/果蔬批發價、產地價、產量統計、進口量 |
| 漁業署 (FA) | 200+ | 漁獲量、養殖、拍賣魚價、漁港、漁船 |
| 林業及自然保育署 (FANC, 前林務局) | 150+ | 森林資源調查、保育類動植物名錄、國家森林遊樂區、林班地 |
| 水土保持及農村發展署 (SWCB) | 100+ | 土石流潛勢溪流、水保設施、農村再生 |
| 動植物防疫檢疫署 (BAPHIQ) | 80+ | 動物疫情 (口蹄疫/禽流感)、植物檢疫、農藥/動物用藥 |
| 各區農業改良場 (桃改/苗改/中改/南改/花改/台東/高雄) | 200+ | 區域作物試驗、品種、農技 |
| 各試驗所 (茶/茶/果樹/林試/家畜衛試) | 100+ | 專業作物研究 |
| 涵蓋更新頻率 | — | 每日 (批發價) / 每週 / 每月 (產量) / 每年 (普查) |

## 何時用本 skill

「農業 / 農產品 / 蔬菜 / 水果 / 稻米 / 漁業 / 漁獲 / 養殖 / 林業 / 森林 / 動物 / 植物 / 農藥 / 肥料 / 動物疫病 / 禽流感 / 茶葉 / 茶 / 農會 / 農改場 / 農委會 / 農業部」相關時優先載入. **不適用於**: 個別農場 / 漁戶 (個資 + 商業)、外國農產品市場.

## MCP Tools

### `search_datasets(query, agency?, domain?, limit?)` + `query_rows(...)`

```python
search_datasets(query="蔬菜 批發 行情", agency="農糧署", limit=10)
get_dataset("12345", sample_rows=3)
query_rows(dataset_id="12345",
           where="market='台北一' AND date >= '2024-01-01' AND crop_name LIKE '%高麗菜%'",
           columns=["date","market","crop_name","avg_price","quantity"],
           limit=100)
```

## 範例 query (繁體中文)

| 使用者問題 | 對應做法 |
|---|---|
| 「2024 高麗菜台北一批發價」 | `search_datasets("蔬菜 批發", agency="農糧署")` → query_rows filter 高麗菜 + 台北一 |
| 「鯖魚去年拍賣均價」 | `search_datasets("漁市 拍賣", agency="漁業署")` |
| 「全國稻米 2024 期作產量」 | `search_datasets("稻米 產量", agency="農糧署")` |
| 「2024 禽流感案例」 | `search_datasets("禽流感", agency="動植物防疫檢疫署")` |
| 「茶葉品評記錄 比賽茶」 | `search_datasets("茶 品評", agency="茶業改良場")` |
| 「林業署保育類動物名錄」 | `search_datasets("保育類 名錄", agency="林業及自然保育署")` 或「林務局」(改制前) |
| 「土石流潛勢溪流分布」 | `search_datasets("土石流 潛勢", agency="水土保持")` |
| 「農藥許可證」 | `search_datasets("農藥 許可", agency="動植物防疫檢疫署")` |

## 機關名稱速查 (catalog 全名)

```
農業部                          (2023.08 改制, 前: 行政院農業委員會, 簡稱農委會)
農業部農糧署                    (AFA)
農業部漁業署                    (FA)
農業部林業及自然保育署          (FANC, 前: 林務局)
農業部水土保持及農村發展署      (SWCB, 前: 水土保持局)
農業部動植物防疫檢疫署          (BAPHIQ)
農業部畜牧司
農業部桃園區農業改良場
農業部苗栗區農業改良場
農業部臺中區農業改良場
農業部臺南區農業改良場
農業部高雄區農業改良場
農業部花蓮區農業改良場
農業部臺東區農業改良場
農業部茶業改良場
農業部林業試驗所
農業部家畜衛生試驗所
```

## 主要市場 / 拍賣場

### 蔬果批發市場 (常用 agencies)

```
台北一 (台北市第一果菜批發市場, 萬大路)
台北二 (台北市第二果菜批發市場, 三民路)
板橋   (新北市果菜批發市場)
三重   (新北三重果菜)
台中   (台中果菜批發市場)
高雄   (高雄市果菜批發市場)
+ 全國各縣市果菜市場 ~15 個
```

### 漁市

```
中央漁市場 (北部)
高雄拍賣場 (南部)
東港 / 蘇澳 / 基隆 / 等地方漁市
```

## 最佳實踐

1. **agency 改制混亂**: 「農委會」(舊) vs「農業部」(新), 「林務局」vs「林業及自然保育署」, 兩個都試
2. **市場 dataset 一個市場一張表**: 想跨市場比要 union 多個 dataset
3. **「crop_name」常含品種**: 「高麗菜」「高麗菜 (進口)」「日式高麗菜」, 用 LIKE
4. **價格單位**: kg / 公斤 / 100kg, 看 dataset 注釋
5. **「期作」是術語**: 一期作 (春耕) / 二期作 (秋收), 別當「第一期」誤解
6. **漁獲量 vs 漁獲值**: 公噸 vs 元, 兩種統計都有, 分清楚

## 注意事項

- 颱風或寒害會嚴重影響蔬果批發價, 解釋價格時要看時間 context
- 農糧署 dataset 含**進口配額 / 海關進口量** (跟財政部 dataset 不一致, 兩邊都收)
- 動物疫病通報有「疑似」vs「確診」, 不要混
- **農地買賣**不在本 skill (在 LVR 實價登錄, `tw-opendata-realestate`, 但農地交易資料較少)

## 與其他 skill 的邊界

- **農業政府採購** → `tw-opendata-pcc`, agency LIKE '%農業%'
- **農產地理 / 地段** → `tw-opendata-geo`
- **農作物 / 茶 / 漁業專利** → `tw-opendata-patent`
- **食品安全 (食藥署)** → `tw-opendata-health`
- **農地實價登錄** → `tw-opendata-realestate`
- **林業 / 自然保育環境** → `tw-opendata-environment`
