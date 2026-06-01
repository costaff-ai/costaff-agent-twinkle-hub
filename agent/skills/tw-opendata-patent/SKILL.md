---
name: tw-opendata-patent
description: Query Taiwan TIPO 經濟部智慧財產局 patent gazette via Twinkle Hub MCP. 涵蓋發明專利、新型專利、設計專利, 2018 → 至今 280,000+ 件 (Phase A+B backfill 中)。語意搜尋專利標題/摘要/申請專利範圍 (Qwen3-Embedding-4B), keyword filter 申請人/IPC 分類/公告日期。Use for 台灣專利檢索 / 專利前案調查 / 競爭對手專利分析 / 技術領域專利地圖 / 申請人專利組合分析。繁體中文 corpus, TIPO opdataapi + ftps XML。
license: Source data 政府資料開放授權條款-1版 (經濟部智慧財產局). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_patents` + `get_patent_body` tools.
metadata:
  corpus: patent
  source: TIPO opdataapi + ftps XML
  language: zh-tw
  version: "1.0.0"
---

# tw-opendata-patent — 台灣專利檢索

## Corpus 概況

| 項目 | 值 |
|---|---|
| 時間範圍 | 2018-01 → 至今 (Phase A 已完, Phase B 2018-2023 backfill 進行中) |
| 總筆數 | ~280,000 件 (含發明/新型/設計三類) |
| 語意 embedding | Qwen3-Embedding-4B, 2560 維, title + abstract + claim_1 拼接 |
| 內文存儲 | title_zh, abstract_zh, claim_1, claim_count, IPC 分類, 申請人, 發明人, 公告日 |
| 來源 | TIPO opdataapi (metadata) + ftps://ftp.tipo.gov.tw (XML 全文) |

## 何時用本 skill

「台灣專利 / TIPO / 發明專利 / 新型專利 / 設計專利 / 專利前案調查 / 專利檢索 / IPC 分類 / 智慧財產局」相關時優先載入。**不適用於**：中國/美國/歐洲/日本/PCT 國際專利 (本 corpus 純台灣本國案)、商標、著作權 (智財局轄但不同 dataset)、專利訴訟 (見 `tw-opendata-judicial` case_type="民事" + court_code="*智*")。

## MCP Tools

### `search_patents(query, ...)` — 主要查詢

```python
search_patents(
    query: str,                       # 語意搜尋 (title + abstract + claim_1)
    title_contains: str = None,       # 標題含子字串
    abstract_contains: str = None,    # 摘要含子字串
    claim_contains: str = None,       # 申請專利範圍含子字串
    applicant: str = None,            # 申請人 (公司名 / 個人), e.g. "台積電" "TSMC"
    ipc_class: str = None,            # IPC 主分類, e.g. "H01L" (半導體裝置)
    patent_type: str = None,          # 發明 / 新型 / 設計
    notice_date_from: str = None,     # YYYYMMDD 公告日起
    notice_date_to: str = None,
    limit: int = 20,
)
```

回 hit: `patent_no`, `title_zh`, `abstract_zh`, `claim_1` (節錄), `applicant`, `ipc_class_list`, `notice_date`, `similarity` 。

### `get_patent_body(patent_no)` — 取完整專利

```python
get_patent_body("I812345")
```

回完整 patent body: 全部 claims (numbered list), full abstract, applicant 列表, inventor 列表, IPC 全分類, priority 資訊, drawings 數量。

## 範例 query

| 使用者問題 | 對應 call |
|---|---|
| 「台積電最近 3 年 EUV 微影相關專利」 | `search_patents("極紫外光微影 EUV", applicant="台積電", notice_date_from="20230101")` |
| 「H01L 類 5 奈米節點發明專利」 | `search_patents("5 奈米 製程", ipc_class="H01L", patent_type="發明")` |
| 「鴻海手機散熱專利」 | `search_patents("手機 散熱", applicant="鴻海")` |
| 「找這件全文 → I812345」 | `get_patent_body("I812345")` |
| 「電池正極材料相關專利」 | `search_patents("鋰電池 正極材料")` |
| 「特斯拉 in 台灣的設計專利」 | `search_patents("", applicant="特斯拉", patent_type="設計")` |

## IPC 主分類速查（最常見前 10）

```
A    人類生活必需（醫藥、農業、食品）
B    作業；運輸
C    化學；冶金
D    紡織；造紙
E    固定建築
F    機械工程
G    物理（含光學、計算）
H    電學（含半導體 H01L、電通信 H04）
A61  醫學
H01L 半導體裝置
H04  電通信
G06  計算
```

完整 IPC 8 大類見 [WIPO IPC](https://www.wipo.int/classifications/ipc/)。

## patent_no 格式

- **發明專利**: `I` + 6 數字, e.g. `I812345`
- **新型專利**: `M` + 6 數字, e.g. `M654321`
- **設計專利**: `D` + 6 數字, e.g. `D200123`

## 最佳實踐

1. **applicant 用簡稱可能漏抓**：「台積電」抓得到, 但官方註冊可能是「台灣積體電路製造股份有限公司」, 兩個都試
2. **IPC 分類 ≠ 技術領域**：IPC 是 patent office 分類, 不全等於商業領域 — semantic query 補
3. **claim_1 是核心**：要看技術 scope, claim_1 比 abstract 更精準（abstract 較行銷化）
4. **2018 之前的不在 corpus**：1991-2017 的台灣專利目前缺, 想查要去 [TIPO Global Patent Search](https://twpat.tipo.gov.tw/)
5. **不要拿英文 query**：corpus 全是繁體中文, 用「半導體製程」不要用「semiconductor process」

## 注意事項

- TIPO Phase B (2018-2023) backfill 仍在進行中, 部分早期月份可能尚未全 ship
- claim_1 是「獨立項」, 一件專利通常有 5-30 個 claim — `get_patent_body` 才能拿全部
- 申請人有時是「事務所」而非真正申請人（早期常見, 後者要查 inventor）

## 與其他 skill 的邊界

- **商標 / 著作權** → 不在本 corpus
- **專利訴訟 / 智財法院判決** → `tw-opendata-judicial`, `court_code="IPCV"` (智慧財產及商業法院)
- **海外專利** → 不支援, 建議 EPO Espacenet / USPTO Patent Search / Google Patents
- **學術技術趨勢** → 結合 `tw-opendata-general` 找科技部相關 dataset
