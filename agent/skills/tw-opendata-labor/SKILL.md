---
name: tw-opendata-labor
description: Query Taiwan labor & employment OpenData via Twinkle Hub MCP. 涵蓋勞動部 (MOL) 勞動條件/職業安全/工會;勞保局 (BLI) 勞工保險/勞退/職災給付;就業安定基金;職訓統計;主計總處全國薪資/受僱員工/失業率 (CPI/PPI 也在 finance skill);勞動及職業安全衛生研究所 (ILOSH) 職災調查/職業病. Use for 薪資查詢 / 就業統計 / 失業率 / 勞保給付 / 職災 / 工時 / 勞資爭議 / 基本工資歷史 / 外勞統計. 繁體中文 corpus.
license: Source data 政府資料開放授權條款-1版 (勞動部 + 勞保局 + 主計總處 + ILOSH). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_datasets` + `query_rows` tools.
metadata:
  corpus: labor
  source: 勞動部 + 勞工保險局 + 行政院主計總處 + 勞動及職業安全衛生研究所
  language: zh-tw
  domain: labor
  version: "1.0.0"
---

# tw-opendata-labor — 勞動就業資料

## Corpus 概況

| 主管機關 | dataset 數量 (~) | 典型內容 |
|---|---|---|
| 勞動部 (MOL) | 400+ | 勞動條件、職安衛、工會、勞資爭議、職訓 |
| 勞工保險局 (BLI) | 200+ | 勞保給付、勞退、職災給付、被保險人數 |
| 行政院主計總處 | 300+ | 全國薪資、受僱員工人數、失業率、人力資源調查 |
| 勞動及職業安全衛生研究所 (ILOSH) | 100+ | 職災調查、職業病、暴露評估 |
| 勞動部勞動力發展署 | 200+ | 就業輔導、職訓、技能檢定、外勞管理 |
| 涵蓋更新頻率 | — | 每月 (薪資/失業率) / 每季 / 每年 |

## 何時用本 skill

「勞動 / 薪資 / 就業 / 失業 / 勞保 / 勞退 / 職災 / 工會 / 工時 / 基本工資 / 加班費 / 勞資爭議 / 職訓 / 外勞 / 移工 / 勞動部 / 勞保局 / 主計總處 (人力)」相關時優先載入. **不適用於**: 個別公司薪資揭露 (商業, 上市 ESG 報告除外, 後者用 `tw-opendata-finance`)、外國就業市場.

## MCP Tools

### `search_datasets(query, agency?, domain?, limit?)` + `query_rows(...)`

## 範例 query (繁體中文)

| 使用者問題 | 對應做法 |
|---|---|
| 「2024 全國平均薪資」 | `search_datasets("受僱員工 薪資", agency="行政院主計總處")` |
| 「歷年基本工資調整」 | `search_datasets("基本工資", agency="勞動部")` |
| 「製造業職災案件 2024」 | `search_datasets("職業災害 製造業", agency="勞動部")` |
| 「全國失業率歷史」 | `search_datasets("失業率 月", agency="行政院主計總處")` |
| 「外勞 (移工) 各國人數」 | `search_datasets("外籍移工 國籍", agency="勞動力發展署")` |
| 「勞退新制提繳人數」 | `search_datasets("勞退 提繳", agency="勞工保險局")` |
| 「勞資爭議調解案件」 | `search_datasets("勞資爭議", agency="勞動部")` |
| 「最低工資與CPI對照」 | 雙 skill: `tw-opendata-labor` + `tw-opendata-finance` (CPI 在 finance) |

## 機關名稱速查 (catalog 全名)

```
勞動部                            (MOL, 前: 行政院勞工委員會 / 勞委會)
勞動部勞工保險局                  (BLI)
勞動部勞動力發展署
勞動部職業安全衛生署
勞動部勞動及職業安全衛生研究所    (ILOSH)
勞動部勞動基金運用局
行政院主計總處                    (人力資源/薪資相關)
```

## 重要指標速查

```
基本工資       現行 (2024) 月薪 NT$27,470 / 時薪 NT$183
勞保普通事故   失能 / 老年 / 死亡 / 生育 / 傷病 五大給付
勞退 (新制)    雇主 6% + 勞工自願 0-6%
失業率定義     15+ 歲願意工作可工作 而未工作之比例
受僱員工統計   工業及服務業薪資 (主計總處每月發布)
人力資源調查   勞動參與率/就業率/失業率 (每月)
職災給付       醫療/傷病/失能/死亡 (從勞保 + 雇主)
```

## 最佳實踐

1. **agency 改制**: 「勞委會」(舊) vs「勞動部」(2014+); 「職訓局」vs「勞動力發展署」; 兩個都試
2. **薪資 ≠ 工資 ≠ 報酬**: 薪資多指經常性薪資 (本薪+加給), 工資含獎金, 報酬含勞健保, 看 dataset 注釋
3. **「受僱員工」vs「勞動人口」**: 前者只計受僱受薪, 後者含自營/雇主, 比較時要對齊
4. **失業率有 U1-U6**: 不同定義, 默認是 U3 (有積極尋職)
5. **外勞 = 移工**: 2018 後官方用「移工」, dataset 兩個都收, 搜時兩個試

## 注意事項

- 個別企業薪資不公開 (除非上市公司財報含均薪資揭露, 用 finance skill)
- 「派遣勞工」「部分工時」常分開統計, 解釋時要區分
- 移工資料: 看護工 (家庭/機構) + 產業移工 (製造/營造/農漁)
- 勞動條件法 vs 勞基法 vs 工會法 各管不同事

## 與其他 skill 的邊界

- **勞資爭議訴訟** → `tw-opendata-judicial`, case_type="民事" + search「勞資」
- **勞動部政府採購** → `tw-opendata-pcc`
- **勞動法案** → `tw-opendata-ly`, search「勞動基準法」「勞工保險條例」
- **CPI / 物價** → `tw-opendata-finance` (主計總處)
- **教師薪資 / 公務員退撫** → `tw-opendata-education` + `tw-opendata-general` (人事總處)
