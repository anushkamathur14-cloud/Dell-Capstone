# `src/validation` — validation check library

Deterministic rules used by the LangGraph validation agent. **Start with the full guide:** [`docs/validation_agent.md`](../../docs/validation_agent.md).

## Modules

| File | Purpose |
|------|---------|
| `checks.py` | Context checks (traffic split, arms, metrics) |
| `benchmark_loader.py` | Load parquet benchmark tables by `experiment_id` |
| `benchmark_checks.py` | Delegate to `synthetic_env/validation/checks.py` |
| `world_spec_checks.py` | `configs/world_spec.yaml` constraints (warnings) |
| `llm_diagnostics.py` | Human-readable summary (template or LLM) |

## Quick usage

```python
from src.agent.validation_agent import ValidationAgent

report = ValidationAgent(benchmark_dir="synthetic_env/benchmarks/generated_sanity_calibrated").run(context)
```

See [`docs/validation_agent.md`](../../docs/validation_agent.md) for decision policy, env vars, and API endpoints.
