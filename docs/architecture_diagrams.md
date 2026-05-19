# Architecture Diagrams — Adaptive Experimentation Agent

Visual reference for the system architecture (**Workstream E**). These diagrams
use [Mermaid](https://mermaid.js.org/) and render automatically on GitHub.

**Sources:** `docs/architecture.md`, `docs/skills_catalog.md`,
`docs/validation_agent.md`.

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
        SK["Orchestrator + five skills<br/>Retrieval<br/>Validation<br/>Causal Evaluation<br/>Recommendation<br/>Generation (deferred)"]
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

The orchestrator runs four skills in sequence. **Experiment Generation** exists
in the code but is **deferred** — it is not wired into the v1 path yet.

```mermaid
flowchart LR
    IN["INPUTS<br/>Product telemetry<br/>Configuration space<br/>Domain knowledge"]

    subgraph V1["Canonical v1 — AdaptiveExperimentationOrchestrator"]
        direction LR
        R["Retrieval<br/>parquet adapter"]
        V["Validation<br/>LangGraph — done"]
        C["Causal Evaluation<br/>deterministic stub"]
        RC["Recommendation<br/>heuristic ranking"]
        STOP["Halt run<br/>return rationale"]
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

> **Note on validation:** if the Validation step returns `stop`, the
> orchestrator halts before Causal Evaluation and Recommendation run, and
> emits a rationale instead of a recommendation.
>
> **Slice labels** mirror `docs/skills_catalog.md`:
> Retrieval (Slice A — parquet adapter), Validation (Slice E hardens — already
> done in v1), Causal Evaluation (Slice B deepens — currently a deterministic
> stub), Recommendation (Slice C replaces — currently heuristic), and
> Experiment Generation (Slice D — Phase 2, not wired in).

---

## 3. Observability — LangSmith tracing

**Question answered:** *How do we see what the agent is doing?*

Every step emits a named trace span. The whole run is wrapped in a
`coordinator_run` umbrella span so the team can debug any single execution end
to end.

```mermaid
flowchart TB
    subgraph CR["coordinator_run — umbrella span"]
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

> **Why this matters:** because each span captures inputs, outputs, latency and
> errors, any failed run can be replayed and inspected without re-running the
> pipeline. This is what makes the agent trustworthy to Nicholas and the rest
> of the team.

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
