# `src/recommendation` — recommendation scoring library

Deterministic scoring and ranking used by the LangGraph recommendation agent.  
**Full guide:** [`docs/recommendation_agent.md`](../../docs/recommendation_agent.md).

| File | Purpose |
|------|---------|
| `scoring.py` | Lift-aware score per candidate |
| `ranking.py` | Sort and assign `rank` |
| `input_checks.py` | Pre-rank warnings |
| `llm_explanation.py` | Template or LLM narrative for top pick |

```python
from src.agent.recommendation_agent import RecommendationAgent

report = RecommendationAgent().run(candidates, evaluation={"uncertainty": 0.1})
```
