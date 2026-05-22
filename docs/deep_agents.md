# Deep agents & progressive disclosure (capstone v2)

Aligned with Dell POC guidance: external prompts, tool loops, schema validation, optional sandboxes.

## Layout

| Path | Purpose |
|------|---------|
| `prompts/` | System prompts per agent (markdown, versioned in git) |
| `src/prompts/loader.py` | Progressive disclosure: `minimal` \| `standard` \| `full` |
| `src/tools/` | Programmatic tools (`run_programmatic_baseline`, `execute_analysis_code`, …) |
| `src/agents/causal_agent.py` | Causal subagent (ReAct when `ENABLE_CAUSAL_AGENT_LOOP=true`) |
| `src/evaluation/schema.py` | Pydantic gate — LLM output never enters pipeline unvalidated |

## Causal agent loop

1. **Always** call `run_programmatic_baseline` (deterministic).
2. Optional: `list_analysis_reference` (disclosure panels).
3. Optional: `execute_analysis_code` (local temp-dir sandbox).
4. **Must** finish with `submit_evaluation` JSON → `EvaluationArtifact`.

Default: **stub/programmatic only** (`ENABLE_CAUSAL_AGENT_LOOP=false`) for CI.

## Optional `deepagents` package

```bash
pip install -e ".[deepagents]"
```

`CausalEvaluationAgent.run_deep_agent()` uses `create_deep_agent` when installed; canonical path uses LangGraph `create_react_agent`.

## Env

See `.env.example`: `ENABLE_CAUSAL_AGENT_LOOP`, `PROMPT_DISCLOSURE_LEVEL`, `CAUSAL_AGENT_MAX_ITERATIONS`.

## LangSmith CLI

See [`langsmith_cli.md`](langsmith_cli.md).
