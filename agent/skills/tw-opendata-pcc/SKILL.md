---
name: tw-opendata-pcc
description: Query 政府電子採購網 (PCC, Public Construction Commission) 招標決標公告 via Twinkle Hub MCP. 我們 mirror 行政院公共工程委員會 PCC 半月 XML, 累積 162,000+ 筆 (含招標公告 + 決標公告), 涵蓋 2015-04 至今全國中央/地方/國營事業政府採購。每日 cron 自動更新。可查標案名稱/機關/採購類型/決標金額/得標廠商/聯絡電話/廠商地址/未得標廠商。Use for 政府採購情報 / 廠商商業情報 / 法人 due diligence / 政府支出分析 / 公共工程追蹤 / 標案投資判斷。繁體中文 corpus, PCC 政府電子採購網公開資料。
license: Source data 公開取得方式: PCC 半月 XML 下載 (政府資料開放授權條款-1版). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `query_rows` against `pcc-tender` synthetic dataset.
metadata:
  corpus: pcc
  source: 行政院公共工程委員會 政府電子採購網 (web.pcc.gov.tw)
  language: zh-tw
  dataset_id: pcc-tender
  version: "1.0.0"
---

# tw-opendata-pcc — 政府電子採購網查詢

## Corpus 概況

| 項目 | 值 |
|---|---|
| 總筆數 | 162,189+ (持續每日 cron 增長) |
| 時間範圍 | 2015-04-01 → 至今 (含未來公告日 e.g. 預公告) |
| 公告類型 | 招標公告 (76,590) + 決標公告 (85,599) |
| 涵蓋採購機關 | 全國中央部會 + 縣市政府 + 國營事業 + 行政法人 |
| 同步頻率 | 每日 cron 03:30 fetch + 03:45 build + 03:52 sync GCS |
| 來源 | PCC 半月 XML [web.pcc.gov.tw/tps/tp/OpenData](https://web.pcc.gov.tw/tps/tp/OpenData/showList) |

## 何時用本 skill

「政府採購 / 招標 / 決標 / 標案 / PCC / 公共工程 / 政府支出 / 廠商得標 / 工程契約 / 採購招標 / 標案查詢 / 政府採購網」相關時優先載入。**不適用於**：私人企業招標、海外政府採購、PFI 民間融資招標 (依不同法規)、軍備採購 (機密不公開)。

## MCP Tools

### `query_rows("pcc-tender", where, ...)` — 主要查詢

```python
query_rows(
    dataset_id="pcc-tender",
    where="agency LIKE '%衛福部%' AND announcement_type='決標公告' AND date >= '2024-01-01'",
    columns=["date", "title", "agency", "companies", "award_price"],
    limit=50,
)
```

DuckDB SQL 直接跑 normalised CSV, 16+ 欄位可用。

### `get_dataset("pcc-tender")` — 看 schema + sample

```python
get_dataset("pcc-tender", sample_rows=3)
```

## 主要欄位

```
date                  公告日期 (YYYY-MM-DD)
announcement_type     '招標公告' | '決標公告'
title                 標案名稱
agency                機關名稱 (e.g. 衛生福利部、新北市政府)
agency_id             [預留欄位, XML 多半空白]
job_number            標案案號
companies             得標廠商 ;-joined (僅決標)
filename              source XML 檔名
detail_url            [預留, XML 無 deep link]

-- v1.12+ enrichment ↓
notice_date           決標公告日 (僅決標)
procurement_type      採購方式 (公開招標 / 限制性招標 / 公開取得)
procurement_attr      標的屬性 (工程類 / 財物類 / 勞務類)
award_way             決標方式 (最低標 / 最有利標)
award_price           決標金額 NTD (僅決標)
contact_phone         機關承辦聯絡電話
contact_person        承辦聯絡人
agency_addr           機關地址
bidder_addr           得標廠商地址 (僅決標)
not_obtain_supp_name  未得標廠商 (僅決標)
```

## 範例 query

| 使用者問題 | 對應 call |
|---|---|
| 「衛福部過去 12 個月 5000 萬以上決標」 | `query_rows("pcc-tender", where="agency LIKE '%衛福部%' AND announcement_type='決標公告' AND award_price > 50000000 AND date >= '2024-06-01'", columns=["date","title","companies","award_price"], limit=100)` |
| 「華電聯網最近得標的案子」 | `query_rows("pcc-tender", where="companies LIKE '%華電聯網%' AND announcement_type='決標公告'", limit=50)` |
| 「公開招標 工程類 1 億以上 in 高雄」 | `query_rows("pcc-tender", where="procurement_type='公開招標' AND procurement_attr='工程類' AND award_price > 100000000 AND agency LIKE '%高雄%'")` |
| 「教育部國中校舍工程招標」 | `query_rows("pcc-tender", where="agency LIKE '%教育%' AND title LIKE '%國中%' AND title LIKE '%校舍%' AND announcement_type='招標公告'")` |
| 「2024 中央機關採購 by 廠商」 | `query_rows("pcc-tender", where="date >= '2024-01-01' AND announcement_type='決標公告'", columns=["companies","award_price"])` 再 client-side group by |

## 最佳實踐

1. **`companies` 是 ;-joined**: 多家共同得標時用 `LIKE '%XX%'`, 不要 `=`
2. **`award_price` 是元不是萬**: 5,000 萬 = 50000000 (8 個 0)
3. **`agency` 用模糊 match**: 「衛福部」抓得到「衛生福利部」, 但「衛生福利部全民健康保險署」要 LIKE '%全民健康保險%'
4. **`title` 含關鍵字**: 想找「資訊系統建置」用 `LIKE '%資訊系統%'`
5. **未得標廠商 (`not_obtain_supp_name`) 也有商業情報價值**: 知道誰跟誰競爭
6. **半月 XML lag**: 每月 1/16 號 PCC 公告當期半月檔, 故 2026-05-15 之前的決標約 2026-06-01 才齊
7. **`date` 跨年度過濾優先**: PCC 162k 全部撈 client side 過濾會很慢, 在 SQL where 限縮日期最快

## 注意事項

- 預公告 (date 是未來日) 是合法狀態, 表示「即將招標」, 不是錯誤
- 部分標案因「機密 / 國防 / 國安」不公開, 本 corpus 收不到
- 廠商名有時是「事務所」「聯合行」, 真實主體要查經濟部商業司
- 「最低標」≠「最有利標」, 後者考量品質非純價格 — 兩種採購邏輯不同, 分析時要區分

## 與其他 skill 的邊界

- **政府支出 (預算決算)** → `tw-opendata-general` (主計總處 dataset)
- **採購法 / 工程契約糾紛訴訟** → `tw-opendata-judicial`, court_code 含 "*高行*" 或一般 court_code 加 query 「政府採購」
- **海外採購 / 軍備** → 不在本 corpus
- **廠商商業登記** → `tw-opendata-general` (經濟部商業司 dataset)
- **公共工程履約 / 工程驗收** → 不在本 corpus, 屬於工程主管機關內部
