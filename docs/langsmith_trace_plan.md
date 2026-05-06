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

## Run naming convention (canonical)

Defined in code as `TraceNames` in `src/observability/langsmith_trace.py`:

| Trace name (`name=`) | When it fires |
|----------------------|----------------|
| `benchmark_generation` | Full synthetic parquet generation (`synthetic_env/traced_pipeline.py`) |
| `retrieval_skill` | Loads / assembles benchmark + memory context |
| `validation_skill` | Data-quality gate |
| `causal_evaluation_skill` | Deterministic effect / lift stub |
| `experiment_generation_skill` | Structured candidate proposals (stub today) |
| `recommendation_agent_v1` | Ranking output |
| `coordinator_run` | Full orchestrator-backed pipeline wrapped by coordinator |
| `coordinator_minimal_demo` | Quick smoke: retrieval → validation → recommendation stub |

Minimum viable spans for demos:

1. `benchmark_generation` (optional, when generating data)
2. `retrieval_skill` → `validation_skill` → … → `recommendation_agent_v1`
3. `coordinator_run` or `coordinator_minimal_demo` as umbrella

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

---

## Nested structure

Coordinator runs nest skill runs automatically when decorators record child spans (LangSmith + `traceable`). For precise tree layout, iterate on tagging once real LangGraph wiring lands.
