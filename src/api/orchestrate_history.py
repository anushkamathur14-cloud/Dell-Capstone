"""Demo-grade persistence for ``POST /orchestrate`` (SQLite file, no Postgres required).

Data lives under ``RUN_HISTORY_DB`` (default ``data/demo_orchestrate.sqlite``). On Railway
without a volume the file is **ephemeral** (cleared on redeploy) — fine for demos.
"""

from __future__ import annotations

import json
import os
import re
import sqlite3
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from fastapi.encoders import jsonable_encoder

_UUID_RE = re.compile(
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$",
    re.IGNORECASE,
)


def db_path() -> Path:
    raw = os.getenv("RUN_HISTORY_DB", "data/demo_orchestrate.sqlite")
    return Path(raw)


def init_db() -> None:
    path = db_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(path)
    try:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS orchestrate_runs (
              id TEXT PRIMARY KEY,
              experiment_id TEXT NOT NULL,
              objective TEXT NOT NULL,
              created_at TEXT NOT NULL,
              status TEXT NOT NULL,
              response_json TEXT,
              error_message TEXT
            )
            """
        )
        con.commit()
    finally:
        con.close()


def is_persisted_run_id(run_id: str) -> bool:
    return bool(_UUID_RE.match(run_id.strip()))


def record_orchestrate_success(
    *,
    experiment_id: str,
    objective: str,
    response: dict[str, Any],
) -> str:
    init_db()
    rid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(jsonable_encoder(response))
    con = sqlite3.connect(db_path())
    try:
        con.execute(
            """
            INSERT INTO orchestrate_runs
              (id, experiment_id, objective, created_at, status, response_json, error_message)
            VALUES (?, ?, ?, ?, ?, ?, NULL)
            """,
            (rid, experiment_id, objective, now, "completed", payload),
        )
        con.commit()
    finally:
        con.close()
    return rid


def record_orchestrate_failure(*, experiment_id: str, objective: str, error: str) -> str:
    init_db()
    rid = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    con = sqlite3.connect(db_path())
    try:
        con.execute(
            """
            INSERT INTO orchestrate_runs
              (id, experiment_id, objective, created_at, status, response_json, error_message)
            VALUES (?, ?, ?, ?, 'failed', NULL, ?)
            """,
            (rid, experiment_id, objective, now, error[:8000]),
        )
        con.commit()
    finally:
        con.close()
    return rid


def list_orchestration_summaries(*, limit: int = 100) -> list[dict[str, Any]]:
    init_db()
    con = sqlite3.connect(db_path())
    try:
        rows = con.execute(
            """
            SELECT id, experiment_id, objective, created_at, status
            FROM orchestrate_runs
            ORDER BY datetime(created_at) DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    finally:
        con.close()
    return [
        {
            "run_id": r[0],
            "orchestration_run_id": r[0],
            "experiment_id": r[1],
            "objective": r[2],
            "created_at": r[3],
            "status": r[4],
            "kind": "orchestration",
        }
        for r in rows
    ]


def get_orchestration_detail(run_id: str) -> dict[str, Any] | None:
    if not is_persisted_run_id(run_id):
        return None
    init_db()
    con = sqlite3.connect(db_path())
    try:
        row = con.execute(
            """
            SELECT id, experiment_id, objective, created_at, status, response_json, error_message
            FROM orchestrate_runs WHERE id = ?
            """,
            (run_id,),
        ).fetchone()
    finally:
        con.close()
    if row is None:
        return None
    response = json.loads(row[5]) if row[5] else None
    return {
        "run_id": row[0],
        "orchestration_run_id": row[0],
        "experiment_id": row[1],
        "objective": row[2],
        "created_at": row[3],
        "status": row[4],
        "source": "orchestration_history",
        "response": response,
        "error_message": row[6],
    }
