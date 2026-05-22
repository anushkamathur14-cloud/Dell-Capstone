# Adaptive Experimentation Agent (MVP Starter)

A clean starter repository for a recommendation-first agentic system that turns experiment data into validated insights and ranked next-best experiments.

**Active feature branches:** `experimentation/validation-agent` (workstream B) · `experimentation/recommendation-agent` (workstream D) — see [`docs/EXPERIMENTATION_DEV_PLAN.md`](docs/EXPERIMENTATION_DEV_PLAN.md) §7 for branch notes and merge order. **Agent strategy (A–E, subagents, deep agents, LLM):** [`docs/WORKSTREAM_AGENT_STRATEGY.md`](docs/WORKSTREAM_AGENT_STRATEGY.md). **Deploy API (Railway/Lovable):** [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Purpose

The MVP focuses on:

- data ingestion and contracts,
- validation and deterministic evaluation,
- candidate generation,
- explainable recommendation ranking.

It intentionally avoids autonomous production execution in v1.

## Architecture Summary

The project uses a modular, skill-based design with:

- `src/agent` for orchestration,
- `src/skills` for reusable capabilities,
- `src/data` for contracts and synthetic data scaffolding,
- `src/api` for service exposure,
- `src/config` for environment-based settings.

Reference architecture: `docs/architecture.md`.
Synthetic world blueprint: `docs/world_spec.md`.

## Setup Instructions

### 1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install --upgrade pip
pip install -e ".[dev]"
```

Optional extras:

```bash
pip install -e ".[vector]"   # pgvector
pip install -e ".[llm]"      # LLM validation summaries (langchain-openai)
```

### 3) Configure environment variables

```bash
cp .env.example .env
```

Update values in `.env` for your local environment.

## Run the API

```bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Quick checks:

- `GET /health`
- `GET /`
- `POST /validate/{experiment_id}?objective=day7_retention` — validation agent only
- `POST /recommend/{experiment_id}?objective=day7_retention` — recommendation agent only
- `POST /orchestrate/{experiment_id}?objective=improve_retention` — full pipeline (includes `validation_report` + `recommendation`)

## Validation agent (Workstream B)

The **validation agent** gates experiment data before evaluation and recommendation. It runs:

1. Context checks (traffic split, arms, metrics),
2. Optional benchmark parquet checks (`synthetic_env` quality gates),
3. World-spec constraint warnings,
4. A template or optional LLM diagnostics summary.

**Full documentation:** [`docs/validation_agent.md`](docs/validation_agent.md) (architecture, decision policy, env vars, examples).

Generate benchmark parquets before running benchmark validation:

```bash
python -c "from synthetic_env.pipeline import run_generation; run_generation(output_dir='synthetic_env/benchmarks/generated_sanity_calibrated')"
```

## Recommendation agent (Workstream D)

The **recommendation agent** ranks generated experiment candidates using a lift-aware score, exposes score breakdowns, and produces a template or optional LLM explanation for the top pick.

**Full documentation:** [`docs/recommendation_agent.md`](docs/recommendation_agent.md).

## Where Docs Live

- **Experimentation roadmap (this branch):** [`docs/EXPERIMENTATION_DEV_PLAN.md`](docs/EXPERIMENTATION_DEV_PLAN.md) — phased dev plan, data/mechanism flows
- **Validation agent (Workstream B):** [`docs/validation_agent.md`](docs/validation_agent.md)
- **Recommendation agent (Workstream D):** [`docs/recommendation_agent.md`](docs/recommendation_agent.md)
- Architecture (runtime repo): `docs/architecture.md`
- World spec: `docs/world_spec.md`
- World config: `configs/world_spec.yaml`
- Capstone knowledge base (outline traceability): [`ARCHITECTURE.md`](ARCHITECTURE.md) (phased execution: Foundation → closed loop → optional perception), [`DATA_SOURCES_AND_TOOLS.md`](DATA_SOURCES_AND_TOOLS.md)

## Synthetic Benchmark Environment

The synthetic experimentation subproject lives in `synthetic_env/` and provides a modular simulator-first stack for benchmark generation and validation.

Run end-to-end generation:

```bash
python -c "from synthetic_env.pipeline import run_generation; run_generation()"
```

See `synthetic_env/README.md` for module details, validation approach, and TODOs.

## Legacy Repository Context

- `Dell_Idea Outline_Team X.pdf`: initial project concept document from repository import.

## Next Priorities

1. Implement real retrieval over SQL + memory store.
2. Expand diagnostics and quality gating.
3. Add deterministic evaluation methods and confidence output.
4. Add constrained experiment candidate generation.
5. Strengthen recommendation scoring and explanation traces.
6. Ground synthetic generation with realistic schema + metric logic.
7. Add unit/integration tests across skills and API.
