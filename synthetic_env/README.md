# Synthetic Experimentation Environment (MVP)

We build a realistic synthetic experimentation environment grounded in real metric logic, parameter schemas, and plausible user heterogeneity. The goal is not to replace real-world data, but to create a credible benchmark for evaluating adaptive experimentation workflows and next-best decision systems.

## Objective

Provide a deterministic, auditable benchmark world for:

- generate -> evaluate -> recommend loops,
- baseline policy comparison,
- future agentic orchestration evaluation.

## Scope

- Hybrid simulator-first design (structural + calibrated realism + optional LLM helpers).
- Canonical experiment tables and KPI outputs.
- Validation utilities across structural/statistical/behavioral/decision dimensions.

## Non-Goals

- Full RL environment
- LLM-only row generation
- Production realism claims at user-level fidelity

## Module Layout

- `world_spec/`: typed schema and world config loader
- `synthetic_population/`: segment-based user generation
- `treatment_space/`: arm generation and constraints
- `outcome_simulator/`: exposure, event-driven outcomes, delayed effects
- `validation/`: quality and usefulness checks
- `benchmarks/`: random and heuristic baselines + agent hooks
- `pipeline.py`: end-to-end generation runner

## Stochastic vs Deterministic Components

The environment is intentionally hybrid: explicit deterministic structure plus controlled stochastic sampling.

| Module | Function/Area | Type | Notes |
|---|---|---|---|
| `pipeline.py` | `run_generation(..., seed=...)` | Deterministic control | The seed is the reproducibility entrypoint for the full run. |
| `synthetic_population/generator.py` | `generate_population()` | Stochastic | Uses `rng.choice`, `rng.normal`, and `rng.integers` for segment assignment and user attributes. |
| `treatment_space/generator.py` | `generate_experiment_tables()` | Deterministic | Builds arms from world spec and applies fixed constraints. |
| `outcome_simulator/simulator.py` | `_assign_arms()` | Stochastic | Randomized arm exposure assignment via `rng.choice`. |
| `outcome_simulator/simulator.py` | `_score_outcomes()` | Mixed | Deterministic formulas plus noise (`rng.normal`) and retention draws (`rng.binomial`). |
| `outcome_simulator/simulator.py` | `summarize_metrics()` | Deterministic | Pure aggregation and confidence interval calculations. |
| `validation/checks.py` | Validation checks | Deterministic | Rule-based checks over generated data tables. |

## Run Generation

From repo root:

```bash
python -c "from synthetic_env.pipeline import run_generation; run_generation()"
```

Outputs are written to `synthetic_env/benchmarks/generated/`.

## Run Validation

Validation runs inside pipeline by default and writes `validation_report.parquet`.

## Notebook Demo

Use `synthetic_env/notebooks/synthetic_env_demo.ipynb` to run:

- population generation
- treatment generation
- outcome simulation
- metrics summary
- validation report

## Next TODOs

1. Add more realism knobs for level-2 world behavior.
2. Add richer event logs (session-level records).
3. Add per-segment fairness or harm constraints.
4. Add SDV/SDMetrics comparison as optional diagnostics.
5. Add CLI entrypoint and config overrides.
