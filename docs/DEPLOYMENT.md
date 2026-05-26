# Deployment (Railway API + Lovable frontend)

Host the **Python API** on Railway; point Lovable (or any UI) at the public URL.

Azure / LangSmith env vars: see [`.env.example`](../.env.example), [`azure_openai.md`](azure_openai.md).

---

## Railway

### Start command

```bash
PYTHONPATH=. python -m uvicorn src.api.main:app --host 0.0.0.0 --port ${PORT:-8080}
```

Repo config: `railway.toml`, `nixpacks.toml`, `railpack.json`, `requirements-railway.txt`.

### Variables (minimum)

| Variable | Notes |
|----------|--------|
| `PORT` | Set to **8080** if your public domain uses 8080 |
| `CORS_ALLOW_ORIGINS` | Lovable preview + prod URLs, comma-separated |
| `BENCHMARK_DATA_DIR` | Default: `synthetic_env/benchmarks/generated_sanity_calibrated` |
| Azure keys | See `.env.example` when `ENABLE_VALIDATION_LLM` / generation flags are on |

### Verify

```bash
curl https://YOUR-RAILWAY-DOMAIN/health
curl -X POST "https://YOUR-RAILWAY-DOMAIN/orchestrate/exp_001?objective=improve_retention"
```

---

## Lovable

1. `VITE_API_URL` = Railway HTTPS URL (no trailing slash).
2. Main flow: `POST /orchestrate/{experiment_id}?objective=improve_retention`.
3. Optional: `POST /validate/{experiment_id}?objective=day7_retention`.
4. Surface `validation_report.decision` and `recommendation` from the JSON response.

---

## API routes on `main`

| Method | Path |
|--------|------|
| `GET` | `/health` |
| `POST` | `/validate/{experiment_id}` |
| `POST` | `/orchestrate/{experiment_id}` |

`/recommend` and `/analyze` exist on `experimentation/recommendation-agent` only — not required for a full Lovable demo if you use `/orchestrate`.
