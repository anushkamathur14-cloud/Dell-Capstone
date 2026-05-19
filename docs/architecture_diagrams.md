# Architecture Diagrams — Adaptive Experimentation Agent

Visual reference for the system architecture (**Workstream E — documentation / diagrams**).
These diagrams use [Mermaid](https://mermaid.js.org/) and render automatically on GitHub.

> **Naming:** **Workstream E** = this diagram deliverable. **Slice E** in
> [`implementation_plan_v1.md`](implementation_plan_v1.md) = Quality Gate (validation implementation).

**Sources:** [`docs/architecture.md`](architecture.md), [`docs/agent_architecture.md`](agent_architecture.md),
[`docs/skills_catalog.md`](skills_catalog.md), [`docs/implementation_plan_v1.md`](implementation_plan_v1.md).
Validation deep-dive (when merged): `docs/validation_agent.md` (see PR #6).

---

## 1. System overview — the four layers

**Question answered:** *How is the system structured?*

Raw data enters at the bottom and flows upward, becoming standardized, then
processed by the agent skills, and finally turned into governed decisions.

```mermaid
flowchart BT
    subgraph L1["Layer 1 — Data &amp; Telemetry Backbone"]
        DT["Experiment logs<br/>Config tables<br/>Segment features<br/>Outcome metrics<br/>Behavioral events"]
    end

    subgraph L0["Layer 0 — Data Contracts"]
        DC["Standard objects<br/>context · action<br/>outcome · constraints<br/>history"]
    end

    subgraph L2["Layer 2 — Skill-Based Agent Layer"]
        SK["Orchestrator + four active skills<br/>Retrieval · Validation · Causal Evaluation · Recommendation<br/>Generation deferred (Slice D)"]
    end

    subgraph L3["Layer 3 — Decision &amp; Governance"]
        DG["Recommended experiments<br/>Rationale<br/>Expected impact<br/>Confidence<br/>Approval-ready outputs"]
    end

    L1 --> L0 --> L2 --> L3

    classDef layer fill:#F5EFE0,stroke:#1E2A5E,color:#1E2A5E,stroke-width:1.5px
    classDef content fill:#ffffff,stroke:#1E2A5E,color:#1E2A5E
    class L1,L0,L2,L3 layer
    class DT,DC,SK,DG content
```

> **Why Layer 0 sits between Layer 1 and Layer 2:** the data contracts are the
> *standardization boundary*. Anything below is raw or domain-specific; anything
> above operates on a fixed object schema. This is what lets skills be swapped
> without breaking the rest of the system.

---

## 2. Canonical v1 flow — the main diagram

**Question answered:** *How does a single run execute?*

The orchestrator runs **four skills** in sequence on `main`. **Experiment Generation**
exists in the codebase but is **not wired** into the canonical v1 path (Slice D / Phase 2).

```mermaid
flowchart LR
    IN["INPUTS<br/>Product telemetry<br/>Configuration space<br/>Domain knowledge"]

    subgraph V1["Canonical v1 — AdaptiveExperimentationOrchestrator"]
        direction LR
        R["Retrieval<br/>stub → parquet adapter"]
        V["Validation<br/>stub on main; LangGraph target PR #6"]
        C["Causal Evaluation<br/>deterministic stub"]
        RC["Recommendation<br/>heuristic ranking"]
        STOP["Halt run<br/>raises error"]
        EG["Experiment Generation<br/>Phase 2 — Slice D"]

        R --> V
        V -- "ok" --> C --> RC
        V -- "stop" --> STOP
        RC -.-> EG
    end

    OUT["OUTPUTS<br/>Optimized configs<br/>Experiment reports<br/>Ranked experiments"]

    IN --> R
    RC --> OUT

    classDef skill fill:#1E2A5E,stroke:#1E2A5E,color:#ffffff
    classDef io fill:#ffffff,stroke:#1E2A5E,color:#1E2A5E
    classDef cluster fill:#F5EFE0,stroke:#1E2A5E,color:#1E2A5E
    classDef deferred fill:#E5E1D5,stroke:#9A9A9A,color:#5A5A5A,stroke-dasharray:5 5
    classDef stop fill:#F5EFE0,stroke:#9A2A2A,color:#9A2A2A,stroke-dasharray:3 3

    class R,V,C,RC skill
    class IN,OUT io
    class V1 cluster
    class EG deferred
    class STOP stop
```

> **Note on validation:** if Validation returns `stop`, the orchestrator **raises**
> (`ValueError` on `main`) before Causal Evaluation and Recommendation run — no
> partial `OrchestrationResult` in v1.
>
> **Slice labels** (see `docs/implementation_plan_v1.md`):
> Retrieval (Slice A), Validation (Slice E — hardens), Causal Evaluation (Slice B),
> Recommendation (Slice C), Experiment Generation (Slice D — deferred).

---

## 3. Observability — LangSmith tracing

**Question answered:** *How do we see what the agent is doing?*

Each canonical step emits a named trace span. Use **`CoordinatorAgent.run_full_pipeline`**
for a **`coordinator_run`** umbrella span (optional; direct orchestrator calls omit it).

```mermaid
flowchart TB
    subgraph CR["coordinator_run — umbrella span (optional)"]
        direction TB
        subgraph ORCH["AdaptiveExperimentationOrchestrator"]
            direction LR
            T1["retrieval_skill"]
            T2["validation_skill"]
            T3["causal_evaluation_skill"]
            T4["recommendation_agent_v1"]
            T1 --> T2 --> T3 --> T4
        end
    end

    LS["LangSmith<br/>each node = one trace span<br/>captures inputs, outputs,<br/>latency, errors"]
    CR -. observed by .-> LS

    classDef span fill:#1E2A5E,stroke:#1E2A5E,color:#ffffff
    classDef cluster fill:#F5EFE0,stroke:#1E2A5E,color:#1E2A5E
    classDef tool fill:#ffffff,stroke:#1E2A5E,color:#1E2A5E
    class T1,T2,T3,T4 span
    class CR,ORCH cluster
    class LS tool
```

> **`experiment_generation_skill`** does not appear on canonical v1 runs until Slice D
> is wired into orchestration.

---

## Appendix — Data Contracts at a glance

A quick reference for the standard objects that move between skills (Layer 0).

| Object        | Purpose                                              |
|---------------|------------------------------------------------------|
| `context`     | Who / where / when the decision is being made for    |
| `action`      | The candidate experiment or configuration change     |
| `outcome`     | Observed or predicted result of an action            |
| `constraints` | Hard limits the recommendation must respect          |
| `history`     | Prior experiments and their outcomes                 |

These objects are the *only* thing that crosses skill boundaries, which is what
keeps the system modular.

---
