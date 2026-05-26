#!/usr/bin/env sh
# Railway: public domain port often 8080; if $PORT is unset, default so edge routing matches.
set -e
PORT="${PORT:-8080}"
export PORT
export PYTHONPATH=.
exec python -m uvicorn src.api.main:app --host 0.0.0.0 --port "$PORT"
