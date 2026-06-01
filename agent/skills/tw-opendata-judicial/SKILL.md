---
name: tw-opendata-judicial
description: Query Taiwan Judiciary court decisions (1996 → present, 360+ months, 6M+ cases) via Twinkle Hub MCP. Supports semantic search (Qwen3-Embedding-4B), keyword filters (court_code, case_type, year, jtitle), and LLM-extracted NER fields (winner, outcome, award_amount, sentence). Use for 台灣司法判決 / 裁判書 / 民事 / 刑事 / 行政訴訟 / 判決金額 / 量刑分析 / 法條引用追蹤. 繁體中文 corpus, 司法院公開資料。
license: Source data 政府資料開放授權條款-1版 (司法院). Skill itself Apache-2.0.
compatibility: Requires Twinkle Hub MCP endpoint with `search_judicial` + `get_judicial_full` tools registered.
metadata:
  corpus: judicial
  source: 司法院 data.gov.tw
  language: zh-tw
  version: "1.0.0"
---

# tw-opendata-judicial — 台灣判決書查詢

## Corpus 概況

| 項目 | 值 |
|---|---|
| 時間範圍 | 1996-01 → 至今 (360+ 個月持續累積) |
| 總筆數 | ~6M 件裁判 (台灣全部法院) |
| 語意 embedding | Qwen3-Embedding-4B, 2560 維, chunk-level |
| NER 抽取 | 法條引用 / 字號引用 / 金額 / 當事人 / 律師 / 法官 (LLM 漸進覆蓋) |
| 來源 | 司法院 [data.gov.tw](https://data.gov.tw) JY 系列, 每月 RAR |

## 何時用本 skill

使用者意圖涉及「台灣司法判決 / 裁判書 / 法院判決 / 大法庭 / 民事/刑事/行政訴訟 / 判決金額 / 量刑分析 / 法條引用追蹤」時優先載入。**不適用於**：律師事務所內部文件、未公開判決、外國判決、行政函釋（後者屬於 `tw-opendata-general`）。

## MCP Tools

### `search_judicial(...)` — 主要查詢

```python
search_judicial(
    query: str,                    # 自然語言, e.g. "車禍精神慰撫金"
    jtitle_contains: str = None,   # 案由含此子字串, e.g. "侵權行為損害賠償"
    jfull_contains: str = None,    # 全文 chunk-level keyword, e.g. "酒駕"
    court_code: str = None,        # 4 字代碼, e.g. "TPSV"
    case_type: str = None,         # 民事 / 刑事 / 行政 / 家事 / 少年 / 懲戒
    year_from: int = None,         # 西元年
    year_to: int = None,
    winner: str = None,            # 原告 / 被告 / 上訴人 / 被上訴人 / 公訴方 / 辯方
    outcome_type: str = None,      # 駁回 / 准許 / 部分准許 / 有罪 / 無罪 / 廢棄發回
    limit: int = 20,               # 1-100
)
```

每筆 hit 含: `jid`, `similarity`, `best_chunk_excerpt`, `jtitle`, `jdate`, `court_code`, `jpdf` 。
若 T3 已 process 該月份, 多含 `issue`, `outcome_type`, `winner`, `award_amount`, `sentence`, `key_reasoning`。

### `get_judicial_full(jid)` — 取全文

```python
get_judicial_full("TPSV,113,台上,1234,20241015,1")
```

回完整判決全文 + metadata + T3 欄位 (若有)。

## 範例 query (繁體中文)

| 使用者問題 | 對應 call |
|---|---|
| 「最近 5 件高雄地院關於商標侵權的判決」 | `search_judicial("商標侵權", court_code="KSDV", limit=5)` |
| 「最高法院 2023 年廢棄發回的刑事判決」 | `search_judicial("", court_code="TPSM", case_type="刑事", year_from=2023, year_to=2023, outcome_type="廢棄發回")` |
| 「醫療糾紛原告勝訴 賠償金額」 | `search_judicial("醫療糾紛", winner="原告", limit=20)` → 看 award_amount |
| 「酒駕致死量刑判決」 | `search_judicial("酒駕致死", case_type="刑事")` → 看 sentence |
| 「取判決全文 KSYV,114,智,15,...」 | `get_judicial_full("KSYV,114,智,15,20250812,1")` |

## court_code 對照（常見前 20）

```
TPSV 最高法院 (民)    TPSM 最高法院 (刑)
TPHV 台高院 (民)      TPHM 台高院 (刑)
TPDV 台北地院 (民)    TPDM 台北地院 (刑)
SLDV 士林地院 (民)    SLDM 士林地院 (刑)
KSDV 高雄地院 (民)    KSDM 高雄地院 (刑)
TCDV 台中地院 (民)    TCDM 台中地院 (刑)
TNDV 台南地院 (民)    TNDM 台南地院 (刑)
TPBA 台北高行 (行)    SCDV 新竹地院 (民)
CYEV 嘉義地院 (民)    HLDV 花蓮地院 (民)
PTDV 屏東地院 (民)    TPCC 憲法法庭
```

完整 50+ 代碼參考 [司法院裁判書系統](https://judgment.judicial.gov.tw)。

## 最佳實踐

1. **越具體越精準**：「商標侵權」+ court_code + year_range 比單純「智財案件」效果好 5x
2. **不確定案由先用語意搜尋**：`query="..."` 不指定 jtitle_contains, 看回的 jtitle 再 narrow
3. **T3 欄位非全月有**：若 winner=null 不代表「無贏家」, 是該月還沒 T3 process
4. **PDF 鏈接已內建**：每筆 `jpdf` 是司法院官方 URL, 用戶要 verify 可直接點開
5. **不要 limit=100 後 client 過濾**：semantic 後段已不相關, 浪費 token。先 narrow filter 再 limit 20
6. **「最有利判決」要 explicit**：用 `outcome_type` + `winner` 篩選 + 看 `award_amount`, 不要主觀判斷

## 注意事項

- 判決書是司法院公開資料, 但**當事人姓名**已被遮罩為 X 或代號, 不要嘗試 deanonymize。
- 「實務見解」「通說」「少數說」要看判決全文 (`get_judicial_full`), 不能只看 excerpt。

## 與其他 skill 的邊界

- **行政函釋 / 解釋字號** (e.g. 釋字 748) → `tw-opendata-general`, 不在本 corpus
- **公務員/律師懲戒** → 本 skill 內, `case_type="懲戒"`
- **大法庭、憲法判決** → 本 skill 內, `court_code="TPCC"` (憲法法庭) / "TPSV-大" (民大法庭)
- **比較法 / 外國判決** → 不支援
