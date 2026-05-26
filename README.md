# Adaptive Experimentation Agent (MVP Starter)

A clean starter repository for a recommendation-first agentic system that turns experiment data into validated insights and ranked next-best experiments.

## Purpose

The MVP focuses on:

- data ingestion and contracts,
- validation and deterministic evaluation,
- recommendation ranking from benchmark-derived evidence,
- deferred proposal-generation layer (Slice D / Phase 2).

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
**Deploy API (Railway + Lovable):** [`docs/DEPLOYMENT.md`](docs/DEPLOYMENT.md).

## Setup Instructions

### 1) Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 2) Install dependencies

```bash
pip install --upgrade pip
pip install -e .
```

Optional extras:

```bash
pip install -e ".[vector]"   # pgvector
pip install -e ".[llm]"      # Azure OpenAI via langchain-openai
```

### 3) Configure environment variables

```bash
cp .env.example .env
```

Update values in `.env` for your local environment. Azure OpenAI setup: [`docs/azure_openai.md`](docs/azure_openai.md). Deep agents / prompts / tools: [`docs/deep_agents.md`](docs/deep_agents.md). LangSmith CLI: [`docs/langsmith_cli.md`](docs/langsmith_cli.md).

End-to-end (stub path, no LLM):

```bash
python scripts/run_e2e_canonical.py
```

Enable causal ReAct loop locally: `ENABLE_CAUSAL_AGENT_LOOP=true` (requires Azure + `pip install -e ".[llm]"`).

Opt-in deployment smoke (not CI):

```bash
RUN_AZURE_OPENAI_SMOKE=true python scripts/smoke_azure_openai.py
```

## Run the API

```bash
uvicorn src.api.main:app --reload --host 127.0.0.1 --port 8000
```

Quick checks:

- `GET /health`
- `GET /`
- `POST /validate/{experiment_id}?objective=day7_retention` — validation agent only
- `POST /orchestrate/{experiment_id}?objective=improve_retention` — full pipeline (includes `validation_report`)

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

## Where Docs Live

- Architecture: `docs/architecture.md`
- **v1 implementation plan (team split):** `docs/implementation_plan_v1.md`
- Agent system map / LangSmith: `docs/agent_architecture.md`, `docs/langsmith_trace_plan.md`, `docs/skills_catalog.md`
- **Validation agent (Slice E):** [`docs/validation_agent.md`](docs/validation_agent.md)
- World spec: `docs/world_spec.md`
- World config: `configs/world_spec.yaml`

## Synthetic Benchmark Environment

The synthetic experimentation subproject lives in `synthetic_env/` and provides a modular simulator-first stack for benchmark generation and validation.

Run end-to-end generation:

```bash
python -c "from synthetic_env.pipeline import run_generation; run_generation()"
```

See `synthetic_env/README.md` for module details, validation approach, and TODOs.

## Agent design and LangSmith (v1 onboarding)

Architecture and trace naming for the coordinated multi-skill runtime:

- `docs/implementation_plan_v1.md` — milestones, slices, contracts, acceptance tests
- `docs/agent_architecture.md` — system map, sync pipeline, persistence notes
- `docs/langsmith_trace_plan.md` — env vars and canonical run names
- `docs/skills_catalog.md` — per-skill purpose / inputs / outputs / traces

Minimal traced demo (requires LangSmith vars in `.env`):

```bash
PYTHONPATH=src:. python scripts/run_traced_dummy_flow.py
```

Optional traced synthetic benchmark generation before the coordinator demo:

```bash
PYTHONPATH=src:. python scripts/run_traced_dummy_flow.py --with-benchmark
```

**Dataset**: public LangSmith hub entry for evaluations / benchmarks  
[LangSmith dataset](https://smith.langchain.com/public/5932f940-296c-4e7a-b8fc-662111b8baa3/d)

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
