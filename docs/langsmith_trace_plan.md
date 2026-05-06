# LangSmith trace plan

**Goal**: every logical step appears as a clear, repeatable run in LangSmith so the group can sanity-check pipelines and compare iterations.

Shared public dataset hub (tie-in with capstone evaluations):

- [LangSmith public dataset](https://smith.langchain.com/public/5932f940-296c-4e7a-b8fc-662111b8baa3/d)

---

## Environment (project-wide `.env`)

| Variable | Purpose |
|---------|---------|
| `LANGSMITH_API_KEY` | Authenticate uploads to LangSmith |
| `LANGSMITH_TRACING` | `"true"` to send traces |
| `LANGSMITH_PROJECT` | e.g. `dell-capstone-adaptive-exp-agent` |

Recommended project name convention: **`dell-capstone-adaptive-exp-agent`**.

Backward compatibility: legacy `LANGCHAIN_TRACING_V2` / `LANGCHAIN_API_KEY` may still appear in tooling; prefer `LANGSMITH_*` for new work.

---

## Canonical full pipeline vs smoke minimal flow

These are **different** call paths in code; trace trees should not be compared one-to-one.

| | **Canonical full pipeline** | **Smoke minimal flow** |
|--|----------------------------|-------------------------|
| **Code** | `AdaptiveExperimentationOrchestrator.run` or `CoordinatorAgent.run_full_pipeline` | `CoordinatorAgent.run_minimal_demo_flow` |
| **Umbrella span** | `coordinator_run` (if using coordinator); direct orchestrator calls omit it | `coordinator_minimal_demo` |
| **Child skills** | `retrieval_skill` → `validation_skill` → `causal_evaluation_skill` → `experiment_generation_skill` → `recommendation_agent_v1` | `retrieval_skill` → `validation_skill` → `recommendation_agent_v1` only |
| **Outcome** | `OrchestrationResult` (includes validation, evaluation, candidates, recommendation) | Plain `dict` with `flow: "smoke_minimal"` |

Use smoke flow only for LangSmith wiring checks and onboarding — **not** for benchmark or product evaluation.

---

## Run naming convention (unchanged)

Defined in code as `TraceNames` in `src/observability/langsmith_trace.py`:

| Trace name (`name=`) | When it fires |
|----------------------|----------------|
| `benchmark_generation` | Full synthetic parquet generation (`synthetic_env/traced_pipeline.py`) |
| `retrieval_skill` | Loads / assembles benchmark + memory context |
| `validation_skill` | Data-quality gate |
| `causal_evaluation_skill` | Deterministic effect / lift stub |
| `experiment_generation_skill` | Structured candidate proposals (stub today) |
| `recommendation_agent_v1` | Ranking output |
| `coordinator_run` | Umbrella: full orchestrator-backed pipeline when invoked via coordinator |
| `coordinator_minimal_demo` | Umbrella: smoke path (partial skills) |

Suggested minimum for **full** demos:

1. `benchmark_generation` (optional, when generating data)
2. Under `coordinator_run`: full sequence of five skill names above

---

## How to run locally

```bash
# .env populated (see repo .env.example)
PYTHONPATH=src:. python scripts/run_traced_dummy_flow.py
```

With optional traced benchmark writes:

```bash
PYTHONPATH=src:. python scripts/run_traced_dummy_flow.py --with-benchmark
```

The default script runs the **smoke** path. For the **canonical full pipeline** with a `coordinator_run` span, invoke `CoordinatorAgent.run_full_pipeline` (or the API `POST /orchestrate/...`, which uses the orchestrator directly).

---

## Nested structure

Coordinator runs nest skill runs when `traceable` records child spans. For precise tree layout, refine tags later; **no LangGraph nodes in v1 scaffold**.
