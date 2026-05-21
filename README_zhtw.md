# CoStaff Twinkle Hub Agent

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.0-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![costaff.agent.json](https://img.shields.io/badge/costaff-compatible-blue.svg)](https://github.com/costaff-ai/costaff)

**繁體中文** | [English](./README.md)

**CoStaff Twinkle Hub Agent** 是基於 **Google ADK** 與 **A2A 協議** 打造的台灣開放資料專員 Agent。它透過 [Twinkle Hub](https://hub.twinkleai.tw/) 統一 MCP 介面，跨 19 個領域、52,960 筆台灣政府開放資料集進行搜尋、查詢、整理，並把整理好的 CSV / JSON 寫入 CoStaff 共享工作區，供下游分析 Agent（Business Analysis、Coding）直接讀取。

> *「我幫你找對的台灣資料、撈剛好夠用的內容、乾淨地存下來、把路徑交出去。」*

設計為 [CoStaff](https://github.com/costaff-ai/costaff) 平台的 external agent，也可以獨立運行或整合任何相容 A2A 的系統。

---

## 目錄

- [運作原理](#運作原理)
- [特色](#特色)
- [架構](#架構)
- [快速開始](#快速開始)
- [環境變數](#環境變數)
- [MCP Tools](#mcp-tools)
- [ADK Skills](#adk-skills)
- [輸出規約](#輸出規約)
- [costaff.agent.json](#costaffagentjson)
- [License](#license)

---

## 運作原理

```
CoStaff Manager Agent
        │
        │  A2A 協議 (/.well-known/agent-card.json)
        ▼
Twinkle Hub Agent  ──►  Twinkle Hub 外部 MCP  ──►  台灣開放資料（19 領域）
        │              (api.twinkleai.tw/mcp/，透過 per-request
        │               FunctionTool 存取 —— 見下方「Race 解法」)
        │
        └──►  in-process 檔案 I/O ──►  /app/data/shared/costaff-agent-twinkle-hub/
                                       └─ <domain>__<dataset_id>__<YYYYMMDD>.csv
                                       └─ <…>.csv.meta.json     （資料溯源 sidecar）
```

每個任務 Agent 都跑這六步：

1. **取得今日日期** — 呼叫 `get_today_utc()`，確保檔名日期戳記正確（**不憑訓練資料猜日期**）。
2. **探索** — 縮小到對的 Twinkle Hub 領域（`opendata-list_domains` + `opendata-search_datasets`）。
3. **檢視** — 確認資料集 schema 與更新頻率（`opendata-get_dataset`）。
4. **取得** — 用 DuckDB SQL 撈過濾後的切片（`opendata-query_rows`）或拉整份資料集（`opendata-materialize_dataset`）。
5. **存檔** — 透過 in-process 工具(`agent/tools/local_io.py`)寫到共享工作區(`save_curated_csv` / `save_curated_json` + `save_meta` 寫 sidecar)。
6. **回報** — 回傳檔案路徑與一行摘要；**不把原始資料 inline 進回應**。

---

## 特色

- **Race 解法後的 MCP 架構** — 外部 Twinkle Hub 透過 **per-request `FunctionTool` ClientSession** 存取(每次工具呼叫各自在 awaited 內開/關 streamable-http MCP session);本地檔案 I/O 走 **in-process**(無獨立 MCP 容器)。零 global `McpToolset` session → 結構性免疫於 to_a2a anyio cancel-scope race(google/adk-python #5729 / #4454)。
- **52,960 筆資料、19 個領域** — 涵蓋環境、不動產、政府採購、醫療衛生、教育、交通⋯⋯。
- **DuckDB SQL 查詢** — 把過濾與排序推到資料層執行，不用整份拉回 client 再篩。
- **資料溯源 sidecar** — 每份 CSV 都附 `<file>.meta.json`，記錄 `dataset_id`、`agency`、`query`、`trace_id`、`fetched_at`、`columns`。下游 Agent 知道自己讀的是什麼。
- **3 個 ADK Skill** — 懶載入的場景操作手冊：`dataset-curation`（通用）、`realestate-lookup`（房價實價登錄）、`aqi-environment`（空氣品質）。
- **可組合於 BA / Coding** — 輸出落在 `/app/data/shared/costaff-agent-twinkle-hub/`，BA Agent 用 `read_csv()` 直接讀。
- **相容 A2A** — 暴露 `/.well-known/agent-card.json` 健康端點。
- **多模型支援** — 原生 Gemini，或任何 LiteLLM 相容的 provider。

---

## 架構

```
costaff-agent-twinkle-hub/
├── agent/
│   ├── agent.py                       # LlmAgent orchestrator
│   ├── agent_a2a.py                   # A2A server 入口（port 8081）
│   ├── instruction/
│   │   ├── __init__.py                # build_instruction() — 替換 placeholder
│   │   └── system.md                  # Agent 系統提示詞
│   ├── mcp_toolsets/__init__.py       # 回 [] —— 零 global McpToolset
│   ├── tools/                         # In-process function tool（取代原獨立 MCP 容器）
│   │   ├── twinkle_hub.py             # 5 個 per-request `opendata-*` 包裝;每次呼叫各自在 awaited body 內開 streamable-http ClientSession
│   │   ├── local_io.py                # 6 個檔案 I/O 函式 in-process 移植:get_today_utc, save_curated_csv/json, save_meta, list_curated, read_curated
│   │   ├── costaff_api.py             # 4 個 manager-core 工具走 httpx shim
│   │   └── _http.py
│   ├── models/                        # Gemini / LiteLLM 模型選擇器
│   ├── skills/                        # ADK Skills（自動探索）
│   │   ├── dataset-curation/SKILL.md
│   │   ├── realestate-lookup/SKILL.md
│   │   └── aqi-environment/SKILL.md
│   ├── progress.py                    # 即時面板 callbacks(before_model / before/after_tool)
│   ├── sub_agents/__init__.py
│   ├── Dockerfile
│   └── requirements.txt
├── mcp/                               # 已 DEPRECATED —— 保留作為歷史;邏輯已移植到 agent/tools/local_io.py
├── docker-compose.yaml                # 1 個 service:agent(原 costaff-mcp-twinkle-hub 容器已移除)
├── .env.template
└── costaff.agent.json                 # Manifest（給 costaff agent add 用）
```

---

## 快速開始

### 前置需求

- Docker 與 Docker Compose
- Twinkle Hub API key（`sk-...`）— 在 <https://hub.twinkleai.tw/login> 登入後取得
- Google Gemini API key **或** 任何 LiteLLM 相容的 provider

### 獨立運行

```bash
git clone https://github.com/costaff-ai/costaff-agent-twinkle-hub.git
cd costaff-agent-twinkle-hub

# 設定密鑰
cp .env.template .env
# 編輯 .env：填入 TWINKLE_HUB_API_KEY 與 GOOGLE_API_KEY

# 建置並啟動
docker compose up -d --build
```

Agent 會在 `http://localhost:8081` 上線。驗證：

```bash
curl http://localhost:8081/.well-known/agent-card.json | jq .name
# → "twinkle_hub_agent"
```

### 透過 A2A 發送測試請求

```bash
curl -X POST http://localhost:8081/ \
  -H "Content-Type: application/json" \
  -d '{
    "jsonrpc": "2.0",
    "id": "1",
    "method": "message/send",
    "params": {
      "message": {
        "messageId": "m1",
        "role": "user",
        "parts": [{"kind": "text", "text": "撈林森測站最近 5 筆 PM2.5 讀值，存到 shared workspace。"}]
      }
    }
  }'
```

CSV 與 meta sidecar 會出現在 `./workspace/shared/costaff-agent-twinkle-hub/`。

### 透過 CoStaff 平台部署

```bash
costaff agent add twinkle-hub --github https://github.com/costaff-ai/costaff-agent-twinkle-hub
# 部署完成後，把密鑰寫入該 agent 的 .env：
echo "TWINKLE_HUB_API_KEY=sk-..." >> ~/.costaff/costaff-agent/twinkle-hub/.env
costaff agent restart twinkle-hub
```

CLI 會自動 clone repo、產生 `compose-fragment.yaml`、把 agent 註冊進 `config.json`、串到共享工作區網路。

**接線模式 — 此 agent 請勿加 `--enable-transfer`。** 它以 **AgentTool**（預設、穩定契約）註冊：Manager 像呼叫 function 一樣呼叫它並取得乾淨的文字結果。`--enable-transfer` **僅**用於 sub-agent 必須接收**多模態圖片輸入**的 agent — 它會把**整個** Manager 切換成 ADK transfer 模式並帶上 session 歷史（見 `costaff-agent-nutrition`）。本 agent 為文字／資料任務型，維持預設即正確且為建議做法。

---

## 環境變數

| 變數 | 必填 | 預設 | 說明 |
|---|---|---|---|
| `TWINKLE_HUB_API_KEY` | ✅ | — | Twinkle Hub 虛擬 API key（`sk-...`），外部 MCP 的 Bearer 認證 |
| `GOOGLE_API_KEY` | ✅（gemini provider） | — | Google Gemini API key |
| `TWINKLE_HUB_EXTERNAL_MCP_URL` | ❌ | `https://api.twinkleai.tw/mcp/` | 只有 Twinkle Hub 改 endpoint 時才覆寫 |
| ~~`MCP_TWINKLE_HUB_LOCAL_URL`~~ | — | — | **已移除** —— 本地 I/O 改為 in-process(無獨立 MCP 容器)|
| `COSTAFF_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` 或 `litellm` |
| `TWINKLE_HUB_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Gemini provider 的模型名稱 |
| `LITELLM_MODEL_NAME` | ❌ | — | LiteLLM provider 的模型名稱 |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API key |
| `WORKSPACE_DIR` | ❌ | `/app/data` | 共享工作區的容器 mount point |
| `SHARED_DIR` | ❌ | `/app/data/shared` | 跨 agent 共享根目錄 |
| `COSTAFF_SHARED_DIR_TWINKLE_HUB` | ❌ | `/app/data/shared/costaff-agent-twinkle-hub` | 本 Agent 在 shared 下的專屬槽 |
| `TWINKLE_HUB_AGENT_MCP_URLS` | ❌ | — | 額外 MCP servers 的 JSON dict（如 manager core MCP） |

---

## MCP Tools

Agent 透過 per-request `FunctionTool` 連外部 Twinkle Hub、檔案 I/O 走 in-process。零 global `McpToolset` —— 見下方「Race 解法」。

### Twinkle Hub 外部(`api.twinkleai.tw/mcp/`,per-request)

下表每個工具都是 `agent/tools/twinkle_hub.py` 的原生 ADK `FunctionTool`,**每次呼叫各自在 awaited 內開 streamable-http `ClientSession`、回傳後關掉**。連字號工具名跟上游 Twinkle Hub MCP 一致,對 LLM 完全相同。

| 工具 | 用途 |
|---|---|
| `opendata-list_domains` | 列出 Twinkle Hub 全部 19 個頂層領域 |
| `opendata-search_datasets` | 用關鍵字、領域、機關、格式等搜尋資料集 |
| `opendata-get_dataset` | 檢視資料集 schema、欄位、列數、授權、新鮮度 |
| `opendata-query_rows` | 對資料集執行 DuckDB SQL(過濾後切片)。內建「抽取守衛」:無 `GROUP BY` 的原始大撈(`limit` 超過 `TWINKLE_HUB_RAW_PULL_LIMIT`)會在結果尾端附強制糾正,導向聚合 SQL,避免趨勢/分布分析撈到非代表性樣本。 |
| `opendata-materialize_dataset` | 強制下載並轉換完整資料集 |

### 本地 I/O(in-process,無 MCP session)

從原 `mcp/tools/data_io.py` 移植到 `agent/tools/local_io.py`。Agent 容器本來就掛了共享 workspace,這 6 個就以純 async function tool 跑 —— **不需要獨立的 `costaff-mcp-twinkle-hub` 容器**。例外被 catch 後回傳 `[ERROR] …` 字串(in-process FunctionTool 若 raise 會炸整個 A2A 請求)。

| 工具 | 用途 |
|---|---|
| `get_today_utc()` | 回傳今日 UTC 日期 `{compact: 'YYYYMMDD', iso: 'YYYY-MM-DD'}`。**每個任務開始一定先呼叫一次**,不准 Agent 自己猜日期。 |
| `save_curated_csv(rows_json, columns_json, filename)` | 把扁平 CSV 寫到 Agent 的 shared 槽。可吃前次呼叫回傳的絕對路徑、也可吃相對路徑。 |
| `save_curated_json(data_json, filename)` | 寫巢狀 / 非表格的 JSON |
| `save_meta(...)` | 寫 `<filename>.meta.json` 資料溯源 sidecar |
| `list_curated(subdir)` | 列出已儲存的檔案(避免重撈同一份資料) |
| `read_curated(filename)` | 讀回自己存過的檔(200 KB 上限) |

### Race 解法(為什麼採 per-request + in-process)

這個 agent 是 google/adk-python #5729 / #4454 的生產解法 —— `to_a2a()` 多代理 + streamable-http MCP 下的 anyio cancel-scope race。Race 程度與「單一 agent 行程內並發的 global `McpToolset` session 數」線性相關:**3 session ⇒ ~84 次/輪、2 session ⇒ ~40 次/輪(仍致命)、1 session ⇒ ~0、0 session 結構性免疫**。本 agent 把外部 Twinkle Hub 改為 per-request `FunctionTool`(ADK 維護者建議的 workaround,經調整以保留精準工具參數)、本地存檔改為 in-process,**全程零 global `McpToolset` session** → 結構性不可能發生 cancel-scope race。此模式建議用於任何「必須使用無法控制的第三方 streamable-http MCP」的 agent。

---

## ADK Skills

`agent/skills/` 下的懶載入場景操作手冊。Agent 自動探索任何 kebab-case 命名且含 `SKILL.md` 的子目錄。Skill 的 metadata（name + description）永遠在 context 中；body 只在模型判斷情境符合時才載入。

| Skill | 觸發場景 | 用途 |
|---|---|---|
| `dataset-curation` | 任何「找 / 撈 / 取」台灣資料的請求（fallback） | 通用 discover→inspect→query→save playbook，含開發中累積的注意事項（英文欄位名、DuckDB 引號、retry 政策） |
| `realestate-lookup` | 實價登錄、房價、不動產、建照、real-estate、property | `realestate_land` 領域：民國年日期格式、總價單位、地段欄位 |
| `aqi-environment` | AQI、PM2.5、空氣品質、河川水質、雨量、環境監測 | `environment` 領域：anchor dataset 28202、字串型別欄位、英文欄位名 |

要新增 skill，把 `<skill-name>/SKILL.md` 丟進 `agent/skills/` 即可，不用改任何 Python。

---

## 輸出規約

每次成功任務都會在 shared 槽產出兩個檔：

```
/app/data/shared/costaff-agent-twinkle-hub/
├── <domain>__<dataset_id>__<YYYYMMDD>[__<slug>].csv
└── <domain>__<dataset_id>__<YYYYMMDD>[__<slug>].csv.meta.json
```

範例：

| 任務 | 檔案 |
|---|---|
| 林森測站 12 個月 PM2.5 歷史 | `environment__28202__20260506__linsen-pm25.csv` + `.meta.json` |
| 大安區 Q1-2024 實價登錄 | `realestate_land__38104__20260506__taipei-daan-q1.csv` + `.meta.json` |

`.meta.json` sidecar 一律包含：

```json
{
  "source_dataset_id": "28202",
  "name": "空氣品質監測月值",
  "agency": "環境部",
  "domain": "environment",
  "columns": ["monitormonth", "sitename", "itemengname", "concentration"],
  "row_count": 12,
  "query": "sitename = '林森' AND itemengname = 'PM2.5' ORDER BY monitormonth DESC",
  "trace_id": "<twinkle-hub-trace>",
  "fetched_at": "2026-05-06T02:43:24+00:00",
  "csv_filename": "environment__28202__20260506__linsen-pm25.csv"
}
```

---

## costaff.agent.json

```json
{
  "protocol_version": "1.0",
  "name": "costaff-agent-twinkle-hub",
  "version": "0.1.0",
  "description": "台灣開放資料的取得與整理。透過 Twinkle Hub MCP 跨 19 個領域搜尋、查詢、materialize 資料集；輸出整理好的 CSV / JSON 到共享工作區。",
  "a2a_service": "agent-twinkle-hub",
  "port": 8081,
  "env_required": ["GOOGLE_API_KEY", "TWINKLE_HUB_API_KEY"],
  "mcp_configurable": true,
  "mcp_env_var": "TWINKLE_HUB_AGENT_MCP_URLS"
}
```

---

## License

採用 Apache 2.0 License 發行。詳見 `LICENSE`。

Twinkle Hub 由 [Twinkle AI](https://hub.twinkleai.tw/) 營運。各資料集著作權屬原發布機關（台灣政府各部會）。每份資料的 `meta.json` 都會記錄來源機關與授權條款。
