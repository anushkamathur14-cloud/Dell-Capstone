# Agent system map (v1)

Recommendation-first adaptive experimentation: five **skills** in sequence, surfaced as separate LangSmith spans. The **orchestrator** owns the canonical wired pipeline; the **coordinator** is the outward entry point and attaches umbrella traces without duplicating business logic.

Public reference dataset (evaluation / examples):

- [LangSmith public dataset — Capstone Adaptive Exp Agent](https://smith.langchain.com/public/5932f940-296c-4e7a-b8fc-662111b8baa3/d)

---

## Coordinator vs orchestrator (role split)

| Component | Role |
|-----------|------|
| **`AdaptiveExperimentationOrchestrator`** (`src/agent/orchestrator.py`) | **Canonical pipeline owner**: calls retrieval → validation → causal evaluation → experiment generation → recommendation in order; builds **`OrchestrationResult`** (experiment context, `validation_report`, `evaluation`, `candidates`, final `recommendation`). |
| **`CoordinatorAgent`** (`src/agent/coordinator.py`) | **Entry + trace grouping**: `run_full_pipeline` **delegates** to the orchestrator (same result type). `run_minimal_demo_flow` is a **smoke-only** shortcut (see below), not the product path. |

Services can call the orchestrator directly (e.g. FastAPI) or go through the coordinator when you want an explicit `coordinator_run` parent span in LangSmith.

---

## Two execution paths (must not be conflated)

| Path | Entry | Skills exercised | Result |
|------|--------|------------------|--------|
| **Canonical full pipeline** | `CoordinatorAgent.run_full_pipeline` or `AdaptiveExperimentationOrchestrator.run` | All five skills | `OrchestrationResult` |
| **Smoke / minimal trace flow** | `CoordinatorAgent.run_minimal_demo_flow` | Retrieval → validation → recommendation only (dummy eval + candidates) | `dict` with `flow: "smoke_minimal"` |

LangSmith: full pipeline uses **`coordinator_run`** (when using the coordinator) plus child skill names; smoke flow uses **`coordinator_minimal_demo`** and **only** fires `retrieval_skill`, `validation_skill`, and `recommendation_agent_v1` — not causal or generation.

---

## High-level flow — canonical full pipeline (synchronous)

```mermaid
flowchart LR
  U[Objective + experiment id] --> O[AdaptiveExperimentationOrchestrator]
  O --> R[Retrieval]
  R --> V[Validation]
  V --> E[Causal Evaluation]
  E --> G[Experiment Generation]
  G --> Rank[Recommendation ranking]
  Rank --> Out[OrchestrationResult]
```

Optional umbrella (same graph, different first hop):

```mermaid
flowchart LR
  U2[Caller] --> C[CoordinatorAgent.run_full_pipeline]
  C --> O2[Orchestrator.run]
  O2 --> Out2[OrchestrationResult]
```

**Default**: sequential, synchronous, single process. Async / distributed orchestration is out of scope for v1.

---

## OrchestrationResult (contract)

Returned on successful full runs (after validation allows proceed). Includes:

- **`experiment`**, **`memory`**, **`metrics`** — context from retrieval layer
- **`validation_report`** — quality gate output
- **`evaluation`** — causal / lift layer output
- **`candidates`** — generation layer output
- **`recommendation`** — ranked next actions

If validation returns `stop`, the orchestrator raises (no partial `OrchestrationResult` in v1).

---

## LangSmith placement

Skill boundaries: `src/agent/traced_steps.py`. Coordinator umbrellas: `CoordinatorAgent`. Canonical names: [`docs/langsmith_trace_plan.md`](langsmith_trace_plan.md).

---

## Persistence (team decision recap)

| Phase | Persistence |
|-------|-------------|
| **v1** | Parquet / structured files (synthetic benchmark + local artifacts); no mandatory Postgres for agent runs. |
| **v1.1+** | Optional Postgres for experiment memory and retrieval-heavy workloads. |

UI (e.g. CopilotKit) is **phase 2** — not required for traced agent demos.

---

## LLM provider (single choice for early protos)

Pick **one** provider for LangChain / LangGraph v1 scaffolding so traces and tooling stay consistent:

| Option | Typical use |
|--------|--------------|
| **OpenAI** (default recommendation) | Fast LangChain ergonomics for structured JSON and graph nodes |
| **Anthropic** | Strong alternative when the team prefers Claude for reasoning-heavy generation |

Defer multi-provider routing until after retrieval + benchmarks are wired.
