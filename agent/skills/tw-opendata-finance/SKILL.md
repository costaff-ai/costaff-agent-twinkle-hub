---
name: tw-opendata-finance
description: Query Taiwan finance / banking / securities / tax OpenData via Twinkle Hub MCP. 涵蓋金管會 (FSC) 銀行/證券/保險/期貨業監管;證交所 (TWSE) 上市公司基本資料/財報/董監事/股價歷史;櫃買中心 (OTC) 上櫃/興櫃公司;集保結算所投資人持股分布;中央銀行 (CBC) 利率/匯率/貨幣供給/外匯存底;財政部稅務/關稅/國庫/國有財產.涵蓋上千家公開發行公司 + 數十年歷史財務數據. Use for 上市公司財報 / 銀行業務統計 / 利率匯率歷史 / 稅務數據 / 保險業 / 投資人結構 / 金融商品檢索. 繁體中文 corpus.
license: Source data 政府資料開放授權條款-1版 (金管會 / 證交所 / 央行 / 財政部). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_datasets` + `query_rows` tools.
metadata:
  corpus: finance
  source: 金管會 (證期局/銀行局/保險局/檢查局) + 證交所 + 櫃買中心 + 集保 + 中央銀行 + 財政部
  language: zh-tw
  domain: economy_business
  version: "1.0.0"
---

# tw-opendata-finance — 金融財稅資料

## Corpus 概況

| 主管機關 | dataset 數量 (~) | 典型內容 |
|---|---|---|
| 金管會 (FSC) | 500+ | 證券/銀行/保險/期貨/投信投顧 業者列表, 處分案件, 法令 |
| 證交所 (TWSE) | 300+ | 上市公司每日/月/年股價、財報、股利、董監事、ESG、TWSE 指數 |
| 櫃買中心 (OTC TPEx) | 150+ | 上櫃 / 興櫃公司類似資料、櫃買指數、上櫃債券 |
| 集保結算所 | 80+ | 投資人持股分布 (股權集中度)、不記名債券、信託 |
| 中央銀行 (CBC) | 200+ | 利率 (重貼現/隔拆/長率)、匯率 (即期/遠期/各幣別)、貨幣供給 M1A/M1B/M2、外匯存底 |
| 財政部 | 800+ | 全國稅收統計、海關進出口、菸酒稅、國庫財政、國有財產 |
| 公平會 | 50+ | 反壟斷案件、聯合行為 |
| 涵蓋更新頻率 | — | 每日 (股價、匯率) / 每週 (利率) / 每月 (進出口、貨幣) / 每季 (財報) / 每年 |

## 何時用本 skill

「銀行 / 證券 / 保險 / 上市公司 / 上櫃 / 股價 / 財報 / 央行 / 利率 / 匯率 / 外匯 / 貨幣供給 / 海關 / 進出口 / 稅務 / 金管會 / 證交所」相關時優先載入. **不適用於**: 個別股票即時報價 (商業數據, 用 Yahoo / TWSE 自家 app)、private equity / 創投未公開公司、海外證券 (NYSE / NASDAQ).

## MCP Tools

### `search_datasets(query, agency?, domain?, limit?)`

```python
search_datasets(query="上市公司 月營收", agency="財團法人中華民國證券櫃檯買賣中心")
```

### `query_rows(dataset_id, where?, columns?, limit)` — DuckDB SQL

```python
query_rows("123456", where="company_id='2330'", columns=["date","revenue","yoy"], limit=12)
```

## 範例 query (繁體中文)

| 使用者問題 | 對應做法 |
|---|---|
| 「台積電 2024 月營收」 | `search_datasets("上市公司 月營收", agency="證交所")` → query_rows filter 公司代號 2330 |
| 「央行 2024 隔夜拆款利率」 | `search_datasets("隔夜拆款", agency="中央銀行")` |
| 「美元台幣匯率歷史」 | `search_datasets("匯率", agency="中央銀行")` |
| 「全國 2023 海關進口前 10 國家」 | `search_datasets("海關 進口 國家別", agency="財政部")` |
| 「上市公司 ESG 報告書」 | `search_datasets("ESG 永續", agency="證交所")` |
| 「金管會 2024 銀行業裁罰」 | `search_datasets("裁罰 處分", agency="金融監督管理委員會")` |
| 「集保 0050 投資人結構」 | `search_datasets("股權分散 集保", agency="集保結算所")` |
| 「全國 2023 各縣市綜所稅」 | `search_datasets("綜所稅 縣市", agency="財政部")` |

## 機關名稱速查 (catalog 全名)

```
金融監督管理委員會                       (金管會 FSC)
金融監督管理委員會證券期貨局             (證期局)
金融監督管理委員會銀行局                 (銀行局)
金融監督管理委員會保險局                 (保險局)
金融監督管理委員會檢查局                 (檢查局)
臺灣證券交易所股份有限公司               (證交所 TWSE)
財團法人中華民國證券櫃檯買賣中心         (櫃買中心 OTC TPEx)
臺灣集中保管結算所股份有限公司           (集保 TDCC)
中央銀行                                 (CBC)
財政部                                   (含關務署 / 國庫署 / 國有財產署)
財政部財政資訊中心
財政部臺北國稅局 (各區國稅局)
公平交易委員會
```

## 公司代號速查 (常用)

```
台積電 2330        鴻海 2317        聯發科 2454
台塑 1301          中鋼 2002        統一 1216
富邦金 2881        國泰金 2882      中信金 2891
台達電 2308        大立光 3008      聯電 2303
HTC 2498           廣達 2382        華碩 2357
```

## 最佳實踐

1. **公司代號用 4 位字串**: "2330" 不是 int 2330 (catalog 多以 string 存)
2. **agency 用全名易抓**: 「證交所」抓不到, 用「臺灣證券交易所股份有限公司」
3. **財報 lag 45 天**: 季報 (4-5-8-11 月) 大都隔季中下旬才公開
4. **匯率有 spot / forward / cross**: 注意要哪種, 不要混
5. **海關進出口 CCC 8 碼**: 用 HS-code 細到 8 位, 詳細品項
6. **稅收統計 vs 申報統計不同**: 前者收到的, 後者報的 (有時差)
7. **「上市」≠ 「上櫃」**: 規模 / 主管市場不同, 別混用 TWSE / TPEx dataset

## 注意事項

- **個股即時股價**不在 OpenData (商業), 想要即時找 TWSE 官方 API 或 Yahoo Finance
- 銀行業 / 保險業 dataset 多為**業界統計** (e.g. 全國放款餘額), 非個別銀行細節
- 金管會裁罰案 dataset 含**業者名稱 + 罰款 + 違規事由**, 可做合規分析
- 海關進出口 dataset 含 **CCC 8 碼 micro 級**, 但有時敏感品項僅開到 4 碼

## 與其他 skill 的邊界

- **金融訴訟 / 銀行訴訟 / 證券訴訟** → `tw-opendata-judicial`, search「銀行法」「證券交易法」
- **金融業政府採購** → `tw-opendata-pcc` (e.g. 公股行庫採購)
- **金融業專利 / fintech 專利** → `tw-opendata-patent`, IPC G06Q (金融商務)
- **金融立法案** → `tw-opendata-ly`, search「金融」「銀行法修正」
- **產業統計 / 製造業 / 商業登記** → `tw-opendata-general` (經濟部商業司, 主計總處)
- **房地產相關金融 (LVR)** → `tw-opendata-realestate`
