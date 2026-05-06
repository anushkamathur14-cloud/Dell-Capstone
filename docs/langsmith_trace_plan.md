# LangSmith trace plan

**Goal:** repeatable runs for review and regression. **Canonical v1** path is the only path used for benchmark evaluation; **smoke** is for wiring checks only.

Shared public dataset:

- [LangSmith public dataset](https://smith.langchain.com/public/5932f940-296c-4e7a-b8fc-662111b8baa3/d)

Team split + milestones: **[`implementation_plan_v1.md`](implementation_plan_v1.md)**.

---

## Environment (project-wide `.env`)

| Variable | Purpose |
|---------|---------|
| `LANGSMITH_API_KEY` | Authenticate uploads |
| `LANGSMITH_TRACING` | `"true"` to send traces |
| `LANGSMITH_PROJECT` | e.g. `dell-capstone-adaptive-exp-agent` |

Legacy LangChain vars may still work alongside; prefer **`LANGSMITH_*`**.

---

## Canonical v1 vs smoke minimal flow

| | **Canonical v1** (benchmarked path) | **Smoke minimal flow** |
|--|--------------------------------------|-------------------------|
| **Code** | `AdaptiveExperimentationOrchestrator.run` or `CoordinatorAgent.run_full_pipeline` | `CoordinatorAgent.run_minimal_demo_flow` |
| **Umbrella** | **`coordinator_run`** if using coordinator; direct orchestrator = no umbrella | **`coordinator_minimal_demo`** |
| **Skills traced** | `retrieval_skill` → `validation_skill` → `causal_evaluation_skill` → `recommendation_agent_v1` | `retrieval_skill` → `validation_skill` → `recommendation_agent_v1` (**no causal**) |
| **Outcome** | `OrchestrationResult` | `{ "flow": "smoke_minimal", … }` |
| **`experiment_generation_skill`** | **Never** on canonical v1 runs (Phase 2) | **Never** |

Do **not** compare smoke traces to canonical v1 timelines.

---

## Run naming convention (`TraceNames` — unchanged literals)

Defined in **`src/observability/langsmith_trace.py`**:

| Trace name | When emitted |
|-----------|----------------|
| `benchmark_generation` | Synthetic parquet pipeline (`synthetic_env/traced_pipeline.py`) |
| `retrieval_skill` | Canonical v1 step 1 |
| `validation_skill` | Canonical v1 step 2 |
| `causal_evaluation_skill` | Canonical v1 step 3 |
| `recommendation_agent_v1` | Canonical v1 step 4 (smoke skips causal but still emits this third child) |
| `experiment_generation_skill` | **Deferred** until Slice D wires proposal layer into orchestration |
| `coordinator_run` | Umbrella over canonical v1 when using coordinator |
| `coordinator_minimal_demo` | Umbrella over smoke path |

**Minimum trace set for a benchmarked demo:** four skill names above (plus optional `coordinator_run`).

---

## How to run locally

Smoke (default script):

```bash
PYTHONPATH=src:. python scripts/run_traced_dummy_flow.py
```

Canonical v1 with coordinator umbrella:

- Call `CoordinatorAgent().run_full_pipeline(...)` **or**
- API `POST /orchestrate/...` (orchestrator only — umbrella omitted unless routed through coordinator).

Benchmark generation (optional, separate subtree):

```bash
PYTHONPATH=src:. python scripts/run_traced_dummy_flow.py --with-benchmark
```

---

## Nested structure

Child spans nest under umbrellas when `@traceable` composes LangSmith contexts. LangGraph visualization is explicitly **post–v1** unless team reopens scope.
