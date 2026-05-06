# Adaptive Experimentation Agent — Implementation Plan v1

## 1. Objective

- Deliver the **first canonical deterministic agent path on top of the frozen benchmark**.
- Keep **LangSmith observability** on explicit skill boundaries (`TraceNames` unchanged where still applicable).
- Use the benchmark as the **fixed evaluation environment**: regressions compare against **`benchmark_v1_delayed_effects_pass`**, not ad-hoc sim tweaks.
- **No** widening of orchestration semantics without team agreement — thin, sequential routing only.

## 2. Frozen baseline

Treat as source of truth (do not “casually” refactor away):

| Asset | Purpose |
|-------|---------|
| `configs/world_spec.yaml` + `docs/world_spec.md` | World definition for synthetic env and validation rules grounding |
| `synthetic_env/benchmarks/generated_sanity_calibrated/` + `BASELINE_NAME.txt` (**`benchmark_v1_delayed_effects_pass`**) | Fixed benchmark parquet + calibration note + sanity summaries |
| `src/observability/langsmith_trace.py` (`TraceNames`) | Stable LangSmith span names |
| Coordinator vs orchestrator split (`docs/agent_architecture.md`) | Who owns umbrellas vs canonical wiring |
| **Smoke vs canonical** semantics (`docs/langsmith_trace_plan.md`) | Onboarding tracer vs benchmarked execution path |

## 3. Canonical workflow

**Canonical v1 (benchmarked path):**

```
retrieval → validation → causal evaluation → recommendation
```

**Smoke flow** (`coordinator_minimal_demo`): retrieval → validation → recommendation only — **tracing / onboarding sanity only**, **not** the benchmark evaluation path.

**Explicitly deferred from canonical v1:**

- **`experiment_generation_skill`** — no span in canonical runs until Phase 2; module remains for Slice D wiring.

Experiment proposal is **future extension** (Slice D). Canonical `OrchestrationResult.candidates` in v1 = **ranking inputs derived from retrieval context** (e.g., arms/metrics envelope), until generation plugs in behind the **same schema contract**.

## 4. Work slices

### Slice A — Ground Truth Data Path

**Goal:** Retrieval reads benchmark artifacts cleanly behind one stable interface (`repository` / adapter pattern).

**Done means:**

- Benchmark tables loaded through one adapter implementation.
- Typed retrieval output (Pydantic or narrow dict schema documented).
- **One acceptance pytest** fixes a fixture Parquet snippet and asserts load + shape contracts.

---

### Slice B — Evaluation / Stats Layer

**Goal:** Causal / statistical evaluation produces auditable summaries and uncertainty grounded in observables.

**Done means:**

- Stable `evaluation` output schema documented and versioned lightly (e.g. `schema_version`).
- Segment-aware summaries (stub path acceptable if schema supports extension).
- **One acceptance pytest** on frozen benchmark-derived fixture.

---

### Slice C — Recommendation Policy

**Goal:** Ranking / scoring of **next-best actions from current evidence** (arms, metrics, evaluation).

**Done means:**

- Scoring dimensions and tie-breakers written down (even if heuristic v1).
- Recommendation bundle schema matches `OrchestrationResult.recommendation` contract.
- **One acceptance pytest** on fixed inputs/evaluation.

---

### Slice D — Proposal Layer (future extension)

**Goal:** Schema-constrained experiment generation (eventually LLM-backed), **same output contract** as eventual `candidates` from proposals.

**Done means:**

- Interface doc + stub or dry-run callable **not wired** into canonical orchestrator yet.
- No change to canonical trace tree without Slice F review.

---

### Slice E — Quality Gate

**Goal:** Validation grounded in `world_spec` constraints and structural checks.

**Done means:**

- `validation_report` schema fixed; rule catalog documented (`go`/`caution`/`stop`).
- **One acceptance pytest** for representative pass/fail cases.

---

### Slice F — Integration & Contracts

**Goal:** Own shared models, orchestration semantics, LangSmith attachment points — **narrow merge gate** on cross-cutting edits.

**Done means:**

- `OrchestrationResult` fields documented; `candidates` semantics (v1 = retrieval-derived ranking envelope vs future = proposals) explicit.
- Trace attachment per step unchanged for existing names; `experiment_generation_skill` documented as inactive in canonical runs until Phase 2.
- One **integration pytest**: full canonical path on artifact fixture produces valid result structure.

---

## 5. Contracts required per slice

Each slice MUST define (in Slice F doc or README appendices):

| Requirement | Deliverable |
|-------------|-------------|
| Objective | 1 paragraph |
| **Input schema** | Types / field list |
| **Output schema** | Types / field list |
| **LangSmith trace name** | As in `TraceNames` (use `none`/`deferred` for Slice D canonical-0) |
| **Acceptance test** | Unique pytest marker or file |
| **Example payload / fixture** | JSON-ish example or small Parquet in `tests/fixtures/` |

### Quick reference (fill as implemented)

| Slice | Trace name (canonical) |
|-------|-------------------------|
| A | `retrieval_skill` |
| E | `validation_skill` |
| B | `causal_evaluation_skill` |
| C | `recommendation_agent_v1` |
| D | `experiment_generation_skill` — **canonical v1:** not emitted |
| F | `coordinator_run` umbrella when using coordinator |

## 6. Recommended build order

**Phase 1 (ship first end-to-end):** **A + E + B + C + F**  
Order within Phase 1: **E** (gate) and **A** (data) in parallel early; then **B**; then **C**; **F** continuously tightens contracts + integration test.

**Phase 2:** **D** plugs into the **same** `candidates` contract; optional `experiment_generation_skill` span reappears in canonical traces once agreed.

**Phase 3 (out of roadmap detail here):** bandits / RL / adaptive allocation — not v1.

## 7. Team operating rules

- **No** widening orchestrator branching / condition forests without Slack + doc amendment.
- **No** silent breaking changes to schemas consumed by downstream slices — bump a small contract note or `schema_version`.
- **Ownership:** one slice lead per horizontal; others PR into that slice’s tests first.
- **Each slice owns** its pytest + fixtures; Integration lives under Slice F initially.
- **LangSmith:** all runs use **`LANGSMITH_PROJECT`** naming convention; spans use **`TraceNames`** literals only — no freestyle names in hot path.
- **Benchmark:** changes to calibrated baseline require explicit “baseline bump” checklist (new parity note), not stealth edits.

## 8. Suggested GitHub issues / milestones

**Milestones**

- `benchmark-v1-locked` (already true — close when team signs off READ)
- `retrieval-real`
- `eval-v1`
- `ranking-v1`
- `validation-v2`
- `generation-v1-llm`

**Lightweight issue template**

- Objective
- Inputs
- Outputs
- Trace name
- Acceptance test (file:test name)
- Owner
- Reviewer

## 9. Immediate next milestone

**First canonical deterministic path end-to-end on frozen benchmark artefacts with LangSmith traces visible for each of:** `retrieval_skill`, `validation_skill`, `causal_evaluation_skill`, `recommendation_agent_v1` (plus optional `coordinator_run` umbrella).

Done when: Slice F integration test passes on checked-in fixture subset + documented run commands + screenshots or trace links archived (owner’s LangSmith OK).

## 10. Out of scope for v1

- RL / bandits inside the agent loop
- UI surfaces (CopilotKit, dashboards productization)
- Production DB migrations / Postgres as hard dependency
- Multi-agent swarm or competing coordinators
- Autonomous production experiment deployment / rollouts
