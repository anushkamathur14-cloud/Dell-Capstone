# Azure AI Foundry — model roles

Your capstone uses an **Azure AI Foundry** project for hosted models. In this repo, each role maps to an environment variable. Values must match **deployment names** in Foundry (often the same as the model id, e.g. `gpt-4o-mini`).

## Role → deployment (your project)

| Role in the system | Env variable | Suggested deployment | Why |
|--------------------|--------------|----------------------|-----|
| Validation narrative (optional; `llm_diagnostics`) | `VALIDATION_LLM_MODEL` | `gpt-4o-mini` | Short summary from fixed checks; cheap, fast; **decision stays in code** |
| Experiment generation (Slice D; structured JSON) | `GENERATION_LLM_MODEL` | `gpt-4o` or `gpt-4.1` | Stronger schema / constraint following (future LLM path) |
| Analyst summaries / recommendation rationale | `RECOMMENDATION_LLM_MODEL` | `gpt-4o-mini` | Same as validation narrative |
| Stat / causal agent (future: code in sandbox) | `STAT_CAUSAL_LLM_MODEL` | `gpt-4.1` or `o4-mini` | Code + multi-step reasoning; sandbox only |
| Orchestration ReAct (future; not v1) | `ORCHESTRATION_LLM_MODEL` | `gpt-4o` or `gpt-4.1` | Tool routing; pipeline gate stays deterministic |
| Embeddings (optional RAG on experiment memory) | `EMBEDDING_MODEL` | `text-embedding-3-small` | Enough for capstone scale (not wired in v1 API) |

**v1 today:** only validation + recommendation narratives (and optional recommendation tool loop) call the LLM when flags are on. Generation, stat/causal ReAct, and embeddings are documented for Foundry setup but mostly deterministic in code.

## Required Azure variables

Set these on **Railway**, **local `.env`**, or Foundry connection strings:

```bash
LLM_PROVIDER=azure
AZURE_OPENAI_ENDPOINT=https://<your-resource>.openai.azure.com/
AZURE_OPENAI_API_KEY=<key-from-foundry>
AZURE_OPENAI_API_VERSION=2024-08-01-preview

VALIDATION_LLM_MODEL=gpt-4o-mini
RECOMMENDATION_LLM_MODEL=gpt-4o-mini
GENERATION_LLM_MODEL=gpt-4o
STAT_CAUSAL_LLM_MODEL=gpt-4.1
ORCHESTRATION_LLM_MODEL=gpt-4o
EMBEDDING_MODEL=text-embedding-3-small

ENABLE_VALIDATION_LLM=true
ENABLE_RECOMMENDATION_LLM=true
```

`LLM_PROVIDER=auto` (default) uses Azure when `AZURE_OPENAI_ENDPOINT` is set; otherwise direct OpenAI.

## LangSmith (optional)

Tracing is independent of Azure vs OpenAI:

```bash
LANGCHAIN_TRACING_V2=true
LANGCHAIN_API_KEY=<langsmith-key>
LANGCHAIN_PROJECT=dell-capstone-validation
```

## Install

```bash
pip install -e ".[llm]"
```

`langchain-openai` supports both `ChatOpenAI` and `AzureChatOpenAI` (used by `src/llm/client.py`).

## Health / smoke

With LLM flags off, the API runs without any Foundry keys. Turn on `ENABLE_VALIDATION_LLM` only after deployments exist and names match the table above.
