# Azure OpenAI (Microsoft Foundry)

## Environment

Copy `.env.example` → `.env` (never commit `.env`). Required:

| Variable | Example | Purpose |
|----------|---------|---------|
| `AZURE_OPENAI_ENDPOINT` | From Azure portal → Keys and Endpoint | Must resolve in DNS |
| `AZURE_OPENAI_API_VERSION` | `2024-12-01-preview` | API version |
| `AZURE_OPENAI_API_KEY` | Portal key | Secret |
| `VALIDATION_LLM_MODEL` | `capstone-mini` | Deployment name (gpt-4o-mini) |
| `GENERATION_LLM_MODEL` | `capstone-standard` | Deployment name (gpt-4.1) |
| `STAT_LLM_MODEL` | `capstone-code` | Deployment name (o4-mini) |
| `ENABLE_VALIDATION_LLM` | `false` | Gate LLM calls in app/tests |

## Code

- Factory: `src/llm/azure_factory.py` — `get_azure_chat_model("validation" | "generation" | "stat")`
- Validation narrative: `src/validation/llm_diagnostics.py` (only when `ENABLE_VALIDATION_LLM=true`)

Install: `pip install -e ".[llm]"`

## Smoke test (opt-in, not CI)

```bash
RUN_AZURE_OPENAI_SMOKE=true python scripts/smoke_azure_openai.py
```

If you see `nodename nor servname provided`, the endpoint hostname is wrong — copy the exact **Endpoint** URL from Azure AI Foundry (often `https://<resource>.openai.azure.com/`).

## Security

- Decisions (`go`/`stop`) and benchmark scoring stay **deterministic code**.
- LLM output is narrative or future proposals; always validate against Pydantic schemas before pipeline use.
