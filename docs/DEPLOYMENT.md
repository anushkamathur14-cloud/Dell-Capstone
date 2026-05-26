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
