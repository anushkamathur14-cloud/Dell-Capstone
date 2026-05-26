# Railway + Lovable (quick fix for 502)

A **502** from `https://…up.railway.app` with `x-railway-fallback: true` usually means the **edge proxy cannot reach your process** — almost always a **port mismatch** or the app never bound to `0.0.0.0`.

## 1. Port (required)

1. Railway → **Variables** → set **`PORT`** to the same number you used when **Generate Domain** (e.g. **8080**).
2. Redeploy. Deploy logs should show: `Uvicorn running on http://0.0.0.0:8080` (same as `PORT`).

This repo’s `railway.toml` / `nixpacks.toml` start command uses **`$PORT`** so it always matches Railway.

## 2. Start command (if you override in the UI)

```bash
PYTHONPATH=. python -m uvicorn src.api.main:app --host 0.0.0.0 --port $PORT
```

Use **`python -m uvicorn`** so the CLI does not depend on PATH.

## 3. CORS for Lovable

Set **Variables** on Railway:

```env
CORS_ALLOW_ORIGINS=https://adaptivegaming.lovable.app
```

Add preview URLs if Lovable uses a different origin (comma-separated, no spaces).

## 4. Smoke test

```bash
curl -sS https://YOUR-RAILWAY-DOMAIN/health
```

Expect `{"status":"ok"}` and HTTP **200**.
