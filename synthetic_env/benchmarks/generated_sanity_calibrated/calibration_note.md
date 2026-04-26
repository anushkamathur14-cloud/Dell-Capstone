# Minimal Calibration Note (Delayed Effects)

## What changed

A single targeted calibration was applied in `synthetic_env/outcome_simulator/simulator.py`:

- `d7_logit` delayed tradeoff coefficient changed from `-0.9 * delayed_tradeoff` to `-2.6 * delayed_tradeoff`.

No new variables, no new arms, and no simulator structural changes were introduced.

## Why

The previous environment already had heterogeneity and plausible arm separation, but delayed effects were slightly below the detectability threshold used by behavioral realism validation (`max |day1 - day7| > 0.03`).

The adjustment increases the long-term penalty on high short-term reward regimes in a controlled way to surface delayed tradeoffs without changing other mechanisms.

## Before vs After (same seed, same population size)

- `day7_retention` spread:
  - Before: `0.0708`
  - After: `0.0623`
- Delayed effect detectability:
  - Before: `False`
  - After: `True`
- Behavioral realism:
  - Before: `False`
  - After: `True`
- Overall validation summary:
  - Before: `False`
  - After: `True`

## Plausibility check

- Arms are still not trivially ranked across all dimensions.
- Retention spread remains moderate (not extreme).
- Heterogeneous effects remain present.
- Delayed effect now exists and is detectable, but does not dominate the full outcome system.

Conclusion: this is a minimal, interpretable calibration that improves benchmark usefulness while preserving compactness and realism.
