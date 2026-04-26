# Synthetic Benchmark Sanity Report

Input directory: `synthetic_env/benchmarks/generated_sanity_calibrated`

## Q1 - Variables: good set, not too many?
- Population rows: 8000
- Feature count (population columns): 11
- Segment mix:
  - casual: 0.358
  - value_seeker: 0.248
  - core: 0.198
  - new_explorer: 0.196
- Verdict: compact and interpretable variable set for v1.

## Q2 - Treatment bundles: plausible and rich enough?
- Number of valid arms: 4
- Arm ids: control, fast_progression, high_challenge, guided_onboarding
- Verdict: enough variation for benchmarking without over-complexity.

## Q3 - Causal assumptions: non-trivial problem?
- Retention spread across arms: 0.0623
- Heterogeneous effects detected: True
- Delayed effects detected: True
- Verdict: non-trivial via arm/segment differences; delayed effects currently too weak for configured threshold.

## Q4 - Outputs credibility
- Validation checks:
  - structural_fidelity: pass=True
  - statistical_fidelity: pass=True
  - behavioral_realism: pass=True
  - decision_usefulness: pass=True
- Metrics summary snapshot:
  - control: conv=0.581, d7=0.589, engagement=49.18, value=1.061
  - fast_progression: conv=0.682, d7=0.651, engagement=59.82, value=1.289
  - guided_onboarding: conv=0.604, d7=0.622, engagement=52.81, value=1.151
  - high_challenge: conv=0.615, d7=0.643, engagement=53.10, value=1.308
- Verdict: outputs look plausible; one validation axis indicates we should strengthen delayed-effect term.