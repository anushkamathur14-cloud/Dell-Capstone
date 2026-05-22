# Statistical analysis reference (standard disclosure)

Use when designing sandbox code:

- Compare arms on retention and conversion with explicit sample sizes.
- Report uncertainty (variance, CI) when available in metrics.
- Prefer simple effect sizes and ranked directions over complex models in v1.
- Document assumptions in code comments, not in final JSON output.

## Hypothesis testing (full disclosure — request `detail=hypothesis`)

- Two-sample tests only when n per arm is sufficient.
- State null/alternative in comments; report p-value and effect direction.

## Regression (full disclosure — request `detail=regression`)

- Linear/logit only for exploratory segmentation; do not overfit small benchmarks.
