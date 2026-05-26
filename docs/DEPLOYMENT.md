# Railway + Lovable (quick fix for 502)

A **502** from `https://…up.railway.app` with `x-railway-fallback: true` usually means the **edge proxy cannot reach your process** — almost always a **port mismatch** or the app never bound to `0.0.0.0`.

## 1. Port (required)

Railway’s **public domain port** must match the port **uvicorn listens on**.

This repo runs **`scripts/run_api_prod.sh`**, which uses **`PORT` from the environment**, or **defaults to `8080`** if `PORT` is unset (fixes the usual 502 when the domain was generated with port **8080** but the app listened elsewhere).

1. Prefer: **Variables** → set **`PORT=8080`** if your domain uses **8080** (recommended).
2. Redeploy. Deploy logs should show: `Uvicorn running on http://0.0.0.0:8080` (or your `PORT`).

## 2. Start command (repo default)

`railway.toml` / `nixpacks.toml` / `railpack.json` use:

```bash
sh scripts/run_api_prod.sh
```

Override in the Railway UI only if debugging.

## 3. CORS for Lovable

If **`CORS_ALLOW_ORIGINS`** is **unset** or **`*`**, the API allows **`https://*.lovable.app`** and **`https://*.lovableproject.com`** (regex). Your app [https://adaptivegaming.lovable.app](https://adaptivegaming.lovable.app) is included.

To lock down production, set:

```env
CORS_ALLOW_ORIGINS=https://adaptivegaming.lovable.app
```

## 4. Smoke test

```bash
curl -sS https://YOUR-RAILWAY-DOMAIN/health
```

Expect `{"status":"ok"}` and HTTP **200**.

## 5. Lovable dashboard — experiment registry (read-only)

These read **`BENCHMARK_DATA_DIR`** (default `synthetic_env/benchmarks/generated_sanity_calibrated`) and expose parquet-backed IDs so the UI matches real benchmark experiments (not mock `exp_392` rows).

| Method | Path | Purpose |
|--------|------|--------|
| `GET` | `/experiments` | All rows from `experiments.parquet` |
| `GET` | `/runs` | **Registry** (`runs`) + **demo orchestrate history** (`orchestrations`, last 100) |
| `GET` | `/runs/{run_id}` | UUID → saved orchestrate payload; otherwise → benchmark snapshot (as before) |
| `POST` | `/orchestrate/{experiment_id}` | Full pipeline; response includes **`run_record_id`** (SQLite row) |

**Demo persistence:** each successful **`POST /orchestrate`** is stored under **`RUN_HISTORY_DB`** (default `data/demo_orchestrate.sqlite`). Failures are stored with `status=failed` and `run_record_id` in the **500** `detail`. On Railway without a disk volume, the DB resets on redeploy — fine for demos; use a mounted volume or Postgres for production.

---

## Build failed (“left the wheelhouse”)

Railway builds this repo with the **root `Dockerfile`** (`[build] builder = "DOCKERFILE"` in `railway.toml`), not Nixpacks, so installs are **`pip install -r requirements-railway.txt`** inside the image.

1. Open **View build logs** and scroll to the **first `ERROR` / `failed` / `Killed`** line.
2. Typical issues: **wheel compile** (the Dockerfile installs `build-essential`), **wrong root directory** in Railway (must be repo root with `Dockerfile`), or **private dependency** access.

### Nixpacks (local only)

`nixpacks.toml` is kept for optional local Nixpacks builds; Railway should **not** use it when the Dockerfile is present and `builder = "DOCKERFILE"` is set.
