# Deployment guide (API + external frontend)

This repo ships the **Python API and agent pipeline**. Host the API on **Railway**, **Colab** (with tunnel), or similar; build the UI in **Lovable** (or any frontend) against the HTTP endpoints.

Cloud deploy is **not automated in this repository** — follow the steps below when you are ready.

---

## 1. API service

### Start command

```bash
PYTHONPATH=. uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8000}
```

Railway sets `PORT` automatically; bind to `0.0.0.0`. **`PYTHONPATH=.`** is required because imports use the `src.*` package prefix.

This repo includes `railway.toml`, `nixpacks.toml`, and `railpack.json` so Railway/Nixpacks use the correct start command (the app is not at `main.py` in the repo root). If deploy still fails, paste **Deploy Logs** and confirm **Settings → Start command** matches the line above.

### Install (Railway)

Nixpacks installs from **`requirements-railway.txt`** (slim production set; includes **`pyarrow`** for parquet). Python is pinned to **3.11** via `nixpacks.toml` and `.python-version`.

Local / full dev install:

```bash
pip install -e ".[dev]"
pip install -e ".[llm]"   # optional, for LLM narratives
```

### Generate benchmark data (recommended before first deploy)

```bash
python -c "from synthetic_env.pipeline import run_generation; run_generation(output_dir='synthetic_env/benchmarks/generated_sanity_calibrated')"
```

Commit the parquets or run generation in a Railway **release command** / one-off job so `BENCHMARK_DATA_DIR` has tables.

---

## 2. Environment variables

| Variable | Required | Notes |
|----------|----------|--------|
| `PORT` | Railway | Set by platform |
| `BENCHMARK_DATA_DIR` | Recommended | Path to parquets (default: `synthetic_env/benchmarks/generated_sanity_calibrated`) |
| `CORS_ALLOW_ORIGINS` | For Lovable | Comma-separated frontend URLs, e.g. `https://your-app.lovable.app` |
| `ENABLE_VALIDATION_LLM` | No | `true` + Azure/OpenAI credentials for validation narratives |
| `ENABLE_RECOMMENDATION_LLM` | No | `true` + credentials for recommendation explanations |
| `ENABLE_RECOMMENDATION_LLM_LOOP` | No | Hybrid tool loop (max 3 iterations); revisions need approval |
| `AZURE_OPENAI_ENDPOINT` | If using Foundry | Azure AI Foundry resource endpoint |
| `AZURE_OPENAI_API_KEY` | If using Foundry | Key from Foundry project |
| `AZURE_OPENAI_API_VERSION` | No | e.g. `2024-08-01-preview` |
| `LLM_PROVIDER` | No | `auto` (default), `azure`, or `openai` |
| `VALIDATION_LLM_MODEL` / `RECOMMENDATION_LLM_MODEL` | If LLM on | **Deployment names** in Foundry — see [`AZURE_FOUNDRY.md`](AZURE_FOUNDRY.md) |
| `ENABLE_CAUSAL_SANDBOX` | No | `true` (default) for extended causal sandbox analysis |
| `DAYTONA_API_KEY` | No | Daytona sandbox; falls back to local subprocess |
| `SANDBOX_PROVIDER` | No | `daytona` (default) |
| `LANGCHAIN_API_KEY` | If LangSmith on | Tracing only (not the Azure chat key) |
| `OPENAI_API_KEY` | If direct OpenAI | Skip when using Azure Foundry |
| `DATABASE_URL` | Future | Not required for current MVP (retrieval uses parquets) |

See `.env.example` for the full list.

---

## 3. Health check

```http
GET /health
```

Response includes `benchmark_parquets_ready` so you can alert if data was not baked into the image.

---

## 4. Endpoints for Lovable (or any UI)

| Method | Path | Purpose |
|--------|------|---------|
| `GET` | `/health` | Liveness + data readiness |
| `POST` | `/validate/{experiment_id}?objective=day7_retention` | Validation only |
| `POST` | `/recommend/{experiment_id}?objective=day7_retention` | Eval + generation + rank |
| `POST` | `/orchestrate/{experiment_id}?objective=improve_retention` | Full pipeline + post-hoc statistical analysis |
| `POST` | `/analyze/{experiment_id}?objective=day7_retention` | Statistical analysis only (after experiment) |

Example (replace host):

```bash
curl -X POST "https://YOUR-RAILWAY-URL/orchestrate/exp_001?objective=improve_retention"
```

Response includes `data_source` (`benchmark` or `stub`), `validation_report`, `evaluation`, and `recommendation`.

---

## 5. Lovable frontend pattern

1. Deploy API → copy public URL.
2. In Lovable, set API base URL env (e.g. `VITE_API_URL`).
3. Call `/orchestrate` for the main flow; surface `validation_report.decision` and `recommendation.top_recommendation`.
4. Set `CORS_ALLOW_ORIGINS` on the API to your Lovable preview/production origin.

---

## 6. What runs in the cloud

| Workstream | In this deploy |
|------------|----------------|
| A | Parquet retrieval (+ stub fallback) |
| B | LangGraph validation agent |
| C | Deterministic causal estimation |
| D | Generation + LangGraph recommendation |
| E | Orchestrator + FastAPI |

LLM nodes remain **optional**; deterministic paths work without Azure or OpenAI. For Foundry setup and model roles, see [`AZURE_FOUNDRY.md`](AZURE_FOUNDRY.md).

---

## 7. Local smoke before deploy

```bash
PYTHONPATH="src:." pytest tests/test_smoke.py tests/test_workstream_be_contracts.py -q
uvicorn src.api.main:app --reload --port 8000
```
