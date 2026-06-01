---
name: tw-opendata-exam
description: Query Taiwan national examinations (國家考試) via Twinkle Hub MCP. 考選部 MOEX dataset 170565 含 64,815 試卷 + 320,663 題目, 涵蓋高普考、司法官、律師、會計師、醫師、教師等 30+ 試類, 2000 年至今。語意搜尋題目內容 (Qwen3-Embedding-4B), keyword filter 試類/年度/科目, 題目層級可單獨檢索。Use for 國考歷屆考題 / 高普考準備 / 律師司法官考題分析 / 證照考古題 / 教師資格考。繁體中文 corpus, 考選部公開資料。
license: Source data 政府資料開放授權條款-1版 (考選部). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_exam`, `search_exam_questions`, `get_exam_paper` tools.
metadata:
  corpus: exam
  source: 考選部 (MOEX dataset 170565)
  language: zh-tw
  version: "1.0.0"
---

# tw-opendata-exam — 國家考試查詢

## Corpus 概況

| 項目 | 值 |
|---|---|
| 試卷數 | 64,815 papers (paper-level metadata) |
| 題目數 | 320,663 questions (question-level chunks) |
| 時間範圍 | 2000 → 至今 (考選部公開歷屆) |
| 試類涵蓋 | 高普考、特考、司法官、律師、會計師、醫師、教師、地方特考、技師、不動產經紀人 等 30+ |
| 語意 embedding | Qwen3-Embedding-4B, 2560 維, **question-level** |
| 來源 | 考選部 [data.gov.tw dataset 170565](https://data.gov.tw/dataset/170565) |

## 何時用本 skill

「國考 / 高普考 / 國家考試 / 律師 / 司法官 / 會計師 / 醫師 / 教師資格考 / 地方特考 / 證照考古題 / 考選部」相關時優先載入。**不適用於**：學測/指考/統測 (升學考試, 另一管道)、研究所考試 (個別校命題)、公司內部測驗。

## MCP Tools

### `search_exam(query, ...)` — 試卷層級搜尋

```python
search_exam(
    query: str,                # 語意搜尋, e.g. "民法物權編題目"
    exam_type: str = None,     # 試類, e.g. "高考三級" "律師" "醫師"
    subject: str = None,       # 科目, e.g. "民法" "刑法" "行政法"
    year_from: int = None,
    year_to: int = None,
    limit: int = 20,
)
```

回試卷 metadata: `paper_id`, `exam_type`, `subject`, `year`, `n_questions`, similarity 。

### `search_exam_questions(query, ...)` — 題目層級搜尋（更細）

```python
search_exam_questions(
    query: str,
    stem_contains: str = None,  # 題幹含此字串, e.g. "默示同意"
    exam_type: str = None,
    subject: str = None,
    year_from: int = None,
    year_to: int = None,
    limit: int = 20,
)
```

回題目: `question_id`, `paper_id`, `stem`（題幹）, `options`（若為選擇題）, `similarity`, 試卷 metadata。

### `get_exam_paper(paper_id)` — 取單張試卷全部題目

```python
get_exam_paper("EXAM2023_高考三級_民法_001")
```

回該試卷全部題目 + metadata。

## 範例 query

| 使用者問題 | 對應 call |
|---|---|
| 「找律師考試最近 5 年民法物權題目」 | `search_exam_questions("民法物權", exam_type="律師", subject="民法", year_from=2020)` |
| 「高考三級行政法 default 函釋題」 | `search_exam_questions("行政函釋", exam_type="高考三級", subject="行政法")` |
| 「醫師國考西醫內科考過什麼」 | `search_exam("內科", exam_type="醫師")` |
| 「司法官考試刑訴傳聞法則的考古題」 | `search_exam_questions("傳聞法則", exam_type="司法官", subject="刑事訴訟法")` |
| 「2024 會計師審計學試題」 | `search_exam("審計學", exam_type="會計師", year_from=2024, year_to=2024)` |

## exam_type 常見值

```
高考三級 / 高考二級 / 高考一級
普考 / 初等考試
特考-警察 / 特考-鐵路 / 特考-地方
司法官 / 律師
會計師 / 記帳士 / 不動產估價師 / 不動產經紀人
醫師 / 牙醫師 / 中醫師 / 藥師 / 護理師
教師資格考 (各教育階段別)
專技高考 / 專技普考
```

## 最佳實踐

1. **paper-level 適合「考過什麼」**, question-level 適合「找特定主題考題」
2. **subject 名稱要精準**：「民法」≠「民事訴訟法」≠「民商法」, 用 `search_exam(query="...")` 先看回的 subject 再 narrow
3. **題目 stem 短**：選擇題題幹通常 < 200 字, 不要期待整段論述 — 申論題才有長題幹
4. **embed 是 question stem** — 找「答案中提到 XX」是 抓不到的, 答案 / 選項不入 embed

## 注意事項

- 部分早期試卷只有 paper-level metadata 沒 question text (考選部 dataset 漸進補齊)
- **不提供官方答案** — 申論題本來無標準解, 選擇題答案需另查考選部公告

## 與其他 skill 的邊界

- **法律相關題目分析 / 引用判例** → 結合 `tw-opendata-judicial` 查實際判決
- **法條本身** → `tw-opendata-general` (catalog 含法務部全國法規)
- **大學/研究所考題** → 不在本 corpus
