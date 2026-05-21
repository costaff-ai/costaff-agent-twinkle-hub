# CoStaff Twinkle Hub Agent

[![Python Version](https://img.shields.io/badge/python-3.12-blue.svg)](https://www.python.org/)
[![Google ADK](https://img.shields.io/badge/Google%20ADK-2.0-orange.svg)](https://github.com/google/adk-python)
[![MCP](https://img.shields.io/badge/MCP-enabled-green.svg)](https://modelcontextprotocol.io/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)
[![A2A Protocol](https://img.shields.io/badge/A2A-protocol-violet.svg)](https://github.com/google/A2A)
[![costaff.agent.json](https://img.shields.io/badge/costaff-compatible-blue.svg)](https://github.com/costaff-ai/costaff)

[繁體中文](./README_zhtw.md) | **English**

**CoStaff Twinkle Hub Agent** is a Taiwan open-data curator agent built on **Google ADK** and the **A2A protocol**. It searches, queries, and curates datasets from [Twinkle Hub](https://hub.twinkleai.tw/) — a unified MCP gateway over 52,960 Taiwan government open datasets across 19 domains — and saves the curated CSV/JSON to the CoStaff shared workspace, ready for downstream analysis agents (Business Analysis, Coding) to consume.

> *"I find the right Taiwan dataset, pull just what's needed, save it cleanly, and hand off the path."*

Designed as an external agent for the [CoStaff](https://github.com/costaff-ai/costaff) platform, it can also run standalone or integrate with any A2A-compatible system.

---

## Table of Contents

- [How It Works](#how-it-works)
- [Features](#features)
- [Architecture](#architecture)
- [Getting Started](#getting-started)
- [Environment Variables](#environment-variables)
- [MCP Tools](#mcp-tools)
- [ADK Skills](#adk-skills)
- [Output Convention](#output-convention)
- [costaff.agent.json](#costaffagentjson)
- [License](#license)

---

## How It Works

```
CoStaff Manager Agent
        │
        │  A2A Protocol (/.well-known/agent-card.json)
        ▼
Twinkle Hub Agent  ──►  Twinkle Hub external MCP  ──►  Taiwan open data (19 domains)
        │              (api.twinkleai.tw/mcp/, accessed via per-request
        │               FunctionTool — see "Race resolution" below)
        │
        └──►  In-process file I/O ──►  /app/data/shared/costaff-agent-twinkle-hub/
                                       └─ <domain>__<dataset_id>__<YYYYMMDD>.csv
                                       └─ <…>.csv.meta.json     (provenance sidecar)
```

For every task, the agent runs a six-step workflow:

1. **Get today's date** — calls `get_today_utc()` so filenames are correctly stamped (never inferred from training data).
2. **Discover** — narrows down to the right Twinkle Hub domain (`opendata-list_domains` + `opendata-search_datasets`).
3. **Inspect** — confirms dataset schema and freshness (`opendata-get_dataset`).
4. **Acquire** — runs DuckDB SQL for filtered slices (`opendata-query_rows`) or pulls full datasets (`opendata-materialize_dataset`).
5. **Save** — writes results to the shared workspace via in-process tools (`save_curated_csv` / `save_curated_json` + `save_meta` for provenance) in `agent/tools/local_io.py`.
6. **Report** — returns file paths and a one-line summary; **never inlines the raw data into the response**.

---

## Features

- **Race-resolved MCP architecture** — the external Twinkle Hub is accessed via **per-request `FunctionTool` ClientSession** (each tool call opens and closes its own streamable-http MCP session inside the awaited body); local file I/O runs **in-process** (no separate MCP container). Zero global `McpToolset` sessions → free of the to_a2a anyio cancel-scope race (google/adk-python #5729 / #4454).
- **52,960 datasets, 19 domains** — environment, real estate, government procurement, health, education, transport, and more.
- **DuckDB SQL queries** — push filtering and ordering into the data layer rather than pulling everything client-side.
- **Provenance sidecars** — every CSV ships a `<file>.meta.json` with `dataset_id`, `agency`, `query`, `trace_id`, `fetched_at`, `columns`. Downstream agents know exactly what they're reading.
- **Three ADK Skills** — lazy-loaded scenario playbooks: `dataset-curation` (generic), `realestate-lookup` (`房價實價登錄`), `aqi-environment` (`空氣品質`).
- **Composable with BA / Coding** — outputs land at `/app/data/shared/costaff-agent-twinkle-hub/`, the path BA Agent reads via `read_csv()`.
- **A2A-compatible** — exposes `/.well-known/agent-card.json` health endpoint.
- **Multi-model support** — Google Gemini natively or any LiteLLM-compatible provider.

---

## Architecture

```
costaff-agent-twinkle-hub/
├── agent/
│   ├── agent.py                       # LlmAgent orchestrator
│   ├── agent_a2a.py                   # A2A server entry (port 8081)
│   ├── instruction/
│   │   ├── __init__.py                # build_instruction() — placeholder substitution
│   │   └── system.md                  # Agent system prompt
│   ├── mcp_toolsets/__init__.py       # Returns [] — no global McpToolset
│   ├── tools/                         # In-process function tools (replace the old separate MCP server)
│   │   ├── twinkle_hub.py             # Per-request `opendata-*` wrappers (5 tools); each opens its own streamable-http ClientSession in the awaited body
│   │   ├── local_io.py                # 6 file-I/O fns ported in-process: get_today_utc, save_curated_csv/json, save_meta, list_curated, read_curated
│   │   ├── costaff_api.py             # 4 manager-core tools via httpx shim
│   │   └── _http.py
│   ├── models/                        # Gemini / LiteLLM model selector
│   ├── skills/                        # ADK Skills (auto-discovered)
│   │   ├── dataset-curation/SKILL.md
│   │   ├── realestate-lookup/SKILL.md
│   │   └── aqi-environment/SKILL.md
│   ├── progress.py                    # Live panel callbacks (before_model / before/after_tool)
│   ├── sub_agents/__init__.py
│   ├── Dockerfile
│   └── requirements.txt
├── mcp/                               # DEPRECATED — kept for history; logic ported to agent/tools/local_io.py
├── docker-compose.yaml                # 1 service: agent (the old costaff-mcp-twinkle-hub container has been removed)
├── .env.template
└── costaff.agent.json                 # Manifest (used by costaff agent add)
```

---

## Getting Started

### Prerequisites

- Docker and Docker Compose
- A Twinkle Hub API key (`sk-...`) — sign in at <https://hub.twinkleai.tw/login> to generate one
- A Google Gemini API key **or** any LiteLLM-compatible provider

### Standalone

```bash
git clone https://github.com/costaff-ai/costaff-agent-twinkle-hub.git
cd costaff-agent-twinkle-hub

# Configure secrets
cp .env.template .env
# Edit .env: fill TWINKLE_HUB_API_KEY and GOOGLE_API_KEY

# Build and run
docker compose up -d --build
```

The agent will be available at `http://localhost:8081`. Verify:

```bash
curl http://localhost:8081/.well-known/agent-card.json | jq .name
# → "twinkle_hub_agent"
```

### Send a test request via A2A

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
        "parts": [{"kind": "text", "text": "Pull 5 most recent PM2.5 readings from 林森 air-quality station and save them."}]
      }
    }
  }'
```

The CSV + meta sidecar will appear under `./workspace/shared/costaff-agent-twinkle-hub/`.

### Via CoStaff Platform

```bash
costaff agent add twinkle-hub --github https://github.com/costaff-ai/costaff-agent-twinkle-hub
# After deploy, set the secret in the agent's per-agent .env:
echo "TWINKLE_HUB_API_KEY=sk-..." >> ~/.costaff/costaff-agent/twinkle-hub/.env
costaff agent restart twinkle-hub
```

The CLI clones the repo, generates `compose-fragment.yaml`, registers the agent in `config.json`, and wires it into the shared workspace network automatically.

**Wiring mode — do NOT pass `--enable-transfer` for this agent.** It is registered as an **AgentTool** (the default, stable contract): the Manager calls it like a function and receives a clean text result. `--enable-transfer` exists *only* for agents whose sub-agent must receive **multimodal image input** — it switches the *entire* Manager into ADK transfer mode and carries session history (see `costaff-agent-nutrition`). This is a text/data-task agent, so the default is correct and recommended.

---

## Environment Variables

| Variable | Required | Default | Description |
|---|---|---|---|
| `TWINKLE_HUB_API_KEY` | ✅ | — | Twinkle Hub virtual API key (`sk-...`), Bearer auth for the external MCP |
| `GOOGLE_API_KEY` | ✅ (gemini provider) | — | Google Gemini API key |
| `TWINKLE_HUB_EXTERNAL_MCP_URL` | ❌ | `https://api.twinkleai.tw/mcp/` | Override only if Twinkle Hub publishes a new endpoint |
| ~~`MCP_TWINKLE_HUB_LOCAL_URL`~~ | — | — | **Removed** — local I/O is now in-process (no separate MCP container) |
| `COSTAFF_AGENT_MODEL_PROVIDER` | ❌ | `gemini` | `gemini` or `litellm` |
| `TWINKLE_HUB_AGENT_MODEL` | ❌ | `gemini-2.5-flash` | Model name for Gemini provider |
| `LITELLM_MODEL_NAME` | ❌ | — | Model name for LiteLLM provider |
| `LITELLM_API_BASE` | ❌ | — | LiteLLM API base URL |
| `LITELLM_API_KEY` | ❌ | — | LiteLLM API key |
| `WORKSPACE_DIR` | ❌ | `/app/data` | Mount point for the shared workspace |
| `SHARED_DIR` | ❌ | `/app/data/shared` | Cross-agent shared root |
| `COSTAFF_SHARED_DIR_TWINKLE_HUB` | ❌ | `/app/data/shared/costaff-agent-twinkle-hub` | This agent's slot under `shared/` |
| `TWINKLE_HUB_AGENT_MCP_URLS` | ❌ | — | JSON dict of extra MCP servers (e.g. manager core MCP) |

---

## MCP Tools

The agent reaches the external Twinkle Hub via per-request `FunctionTool` wrappers and runs file I/O in-process. Zero global `McpToolset` — see "Race resolution" below.

### Twinkle Hub external (`api.twinkleai.tw/mcp/`, per-request)

Each tool below is a native ADK `FunctionTool` in `agent/tools/twinkle_hub.py` that opens its own streamable-http `ClientSession` strictly inside the awaited call body and closes it on return. The hyphenated names match the upstream Twinkle Hub MCP and remain identical to the LLM.

| Tool | Description |
|---|---|
| `opendata-list_domains` | List all 19 top-level Twinkle Hub domains |
| `opendata-search_datasets` | Search datasets by keyword, domain, agency, format, etc. |
| `opendata-get_dataset` | Inspect a dataset's schema, columns, row count, license, freshness |
| `opendata-query_rows` | Run DuckDB SQL against a dataset (filtered slice). Includes a deterministic "extraction guard" that appends a corrective when a no-`GROUP BY` raw pull exceeds the row threshold (`TWINKLE_HUB_RAW_PULL_LIMIT`), nudging the LLM toward aggregate SQL for trend/distribution analysis. |
| `opendata-materialize_dataset` | Force download + transform of a full dataset |

### Local I/O (in-process, no MCP session)

Ported from the former `mcp/tools/data_io.py` into `agent/tools/local_io.py`. The agent container already mounts the shared workspace, so these run as plain async function tools — no separate `costaff-mcp-twinkle-hub` container needed. Errors are caught and returned as `[ERROR] …` strings (an in-process FunctionTool that raises would abort the whole A2A request).

| Tool | Description |
|---|---|
| `get_today_utc()` | Return today's UTC date as `{compact: 'YYYYMMDD', iso: 'YYYY-MM-DD'}`. Always called once at task start; never let the agent guess a date. |
| `save_curated_csv(rows_json, columns_json, filename)` | Write a flat CSV to the agent's shared slot. Accepts the absolute path returned by a prior call as well as a relative path inside the slot. |
| `save_curated_json(data_json, filename)` | Write nested / non-tabular JSON |
| `save_meta(...)` | Write a `<filename>.meta.json` provenance sidecar |
| `list_curated(subdir)` | List previously saved files (avoid re-fetching the same dataset) |
| `read_curated(filename)` | Read back own saved file (200 KB cap) |

### Race resolution (why this is per-request + in-process)

This agent is the production response to google/adk-python #5729 / #4454 (anyio cancel-scope race under `to_a2a()` multi-agent + streamable-http MCP). The race scales with the number of *concurrent global `McpToolset` sessions* held in one agent process; 2+ sessions race fatally, 1 session is ≈0, and 0 sessions is structurally race-free. By moving the external Twinkle Hub to a per-request `FunctionTool` (the ADK maintainer's recommended workaround, adapted to preserve precise tool args) and the local saver to in-process functions, this agent holds **zero global `McpToolset` sessions** — the cancel-scope race cannot occur by construction. The pattern is recommended for any agent that must talk to an unavoidable 3rd-party streamable-http MCP it doesn't control.

---

## ADK Skills

Lazy-loaded scenario playbooks under `agent/skills/`. The agent auto-loads any kebab-case folder containing a `SKILL.md`. The skill metadata (name + description) is always in context; the body loads only when the model decides the scenario applies.

| Skill | Trigger | Purpose |
|---|---|---|
| `dataset-curation` | Default fallback for any "fetch / find / pull" Taiwan data request | Generic discover→inspect→query→save playbook with lessons learned (English column names, DuckDB quoting, retry policy) |
| `realestate-lookup` | 實價登錄, 房價, 不動產, 建照, real-estate, property | `realestate_land` domain: 民國年日期格式、總價單位、地段欄位 |
| `aqi-environment` | AQI, PM2.5, 空氣品質, 河川水質, 雨量, 環境監測 | `environment` domain: anchor dataset 28202, all-string columns, English column names |

To add a new skill, drop a `<skill-name>/SKILL.md` into `agent/skills/`. No code changes needed.

---

## Output Convention

Every successful task produces two files in the shared slot:

```
/app/data/shared/costaff-agent-twinkle-hub/
├── <domain>__<dataset_id>__<YYYYMMDD>[__<slug>].csv
└── <domain>__<dataset_id>__<YYYYMMDD>[__<slug>].csv.meta.json
```

Examples:

| Task | Files |
|---|---|
| 12-month PM2.5 history for 林森 | `environment__28202__20260506__linsen-pm25.csv` + `.meta.json` |
| 大安區 Q1-2024 實價登錄 | `realestate_land__38104__20260506__taipei-daan-q1.csv` + `.meta.json` |

The `.meta.json` sidecar always contains:

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
  "description": "Taiwan open data acquisition and curation. Searches, queries, and materializes datasets from Twinkle Hub MCP across 19 domains; outputs curated CSV/JSON to the shared workspace.",
  "a2a_service": "agent-twinkle-hub",
  "port": 8081,
  "env_required": ["GOOGLE_API_KEY", "TWINKLE_HUB_API_KEY"],
  "mcp_configurable": true,
  "mcp_env_var": "TWINKLE_HUB_AGENT_MCP_URLS"
}
```

---

## License

Distributed under the Apache 2.0 License. See `LICENSE` for details.

Twinkle Hub is operated by [Twinkle AI](https://hub.twinkleai.tw/). Credits to the original dataset publishers (Taiwan government agencies). Each dataset's `meta.json` records its source agency and license.
