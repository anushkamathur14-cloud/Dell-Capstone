# Synthetic World Specification

## Purpose

We build a realistic synthetic experimentation environment grounded in real metric logic, parameter schemas, and plausible user heterogeneity. The goal is not to replace real-world data, but to create a credible benchmark for evaluating adaptive experimentation workflows and next-best decision systems.

This world is designed to be:

- structured,
- auditable,
- modular,
- simple enough for v1 implementation,
- realistic enough for credible generate -> evaluate -> recommend testing.

## Scope and Non-Goals

### Scope

- Controlled simulation for experiments with heterogeneous users.
- Explicit treatment bundles and valid/invalid constraints.
- Event and KPI generation with deterministic formulas plus stochastic noise.
- Validation checks for structural, statistical, behavioral, and decision usefulness.

### Non-Goals

- Full RL environment.
- LLM-only row generation.
- Claims of production-realism at individual behavior granularity.
- Replacing real experimentation data.

## Entities

1. **User/Segment State**: user traits and segment assignments.
2. **Treatment Bundle**: parameterized experiment arm configurations.
3. **Event Process**: session and interaction traces from exposure.
4. **Outcomes/KPIs**: retention, engagement, and monetization proxies.

## User and Segment Variables

### Static attributes

- `user_id` (string): stable identifier.
- `segment_id` (categorical): one of `casual`, `core`, `value_seeker`, `new_explorer`.
- `acquisition_source` (categorical): `organic`, `paid`, `referral`, `cross_sell`.
- `baseline_skill` (float, 0.0-1.0): initial capability level.
- `spend_propensity` (float, 0.0-1.0): latent monetization tendency.

### Slowly changing attributes

- `lifecycle_stage` (categorical): `new`, `maturing`, `established`, `at_risk`.
- `engagement_propensity` (float, 0.0-1.0): long-horizon engagement tendency.
- `friction_tolerance` (float, 0.0-1.0): tolerance for UI and process friction.

### Dynamic attributes

- `recent_activity_score` (float, 0.0-1.0): recent usage momentum.
- `recent_sessions_7d` (int, 0-14): rolling week activity frequency.
- `churn_risk` (float, 0.0-1.0): latent short-term drop-off risk.

### Why these matter

- They create segment heterogeneity and meaningful treatment interactions.
- They support delayed effects and non-trivial tradeoffs.
- They stay compact and interpretable for auditing.

## Treatment Space

### Parameter table

- `difficulty_shift` (continuous, -0.3 to 0.3)
- `reward_rate` (continuous, 0.5 to 2.0)
- `matchmaking_delay_sec` (continuous, 2.0 to 45.0)
- `ui_friction` (bounded continuous, 0.0 to 1.0)
- `progression_speed` (continuous, 0.6 to 1.8)
- `content_exposure_intensity` (continuous, 0.2 to 1.0)
- `onboarding_support` (categorical: `off`, `light`, `guided`)
- `promotion_intensity` (categorical: `none`, `soft`, `aggressive`)

### Invalid/forbidden combinations

- `promotion_intensity=aggressive` with `ui_friction > 0.7`.
- `matchmaking_delay_sec > 35` with `difficulty_shift > 0.2`.
- `reward_rate > 1.8` with `progression_speed > 1.6`.

### Example bundles

- `control`: balanced defaults.
- `fast_progression`: higher progression and reward, moderate friction.
- `high_challenge`: higher difficulty and lower reward, better long-term for core users.
- `guided_onboarding`: strong onboarding support, slightly lower progression speed.

## Event Schema

### Directly observed events

- `session_start`
- `session_end`
- `content_interaction`
- `progression_event`
- `reward_claim`
- `churn_signal`

### Derived metrics

- session_length_minutes
- interaction_count
- progression_count
- reward_claim_rate
- churn_signal_rate

### Outcome drivers

- Session length and interaction count primarily drive engagement KPI.
- Progression and churn signals drive short and medium retention.
- Reward claims and engagement interact to drive monetization proxy.

## KPI Definitions

- `day1_retention` (binary/probability): immediate retention objective.
- `day7_retention` (binary/probability): delayed retention objective.
- `engagement_time` (continuous): immediate + medium horizon behavior.
- `interaction_count` (count): direct activity intensity proxy.
- `monetization_proxy` (continuous): latent value proxy, not direct revenue.
- `satisfaction_proxy` (continuous): soft metric from friction and progression fit.

### Optimization target for v1

Default target: **day7_retention** with constraints on monetization_proxy and satisfaction_proxy floors.

## Causal and Behavioral Assumptions

1. Effects are heterogeneous by segment and baseline traits.
2. `difficulty_shift` has positive effects for high-skill users and negative effects for low-skill users.
3. `ui_friction` hurts low `friction_tolerance` users disproportionately.
4. `reward_rate` boosts short-term engagement but can reduce long-term retention when too high.
5. `progression_speed` and `onboarding_support` interact strongly for new users.
6. Delayed effects exist: some bundles improve day1 but hurt day7 and vice versa.
7. Noise and partial unpredictability are always present.

### Intentional non-trivial patterns

- Local optima: short-term engagement maxima that degrade day7 retention.
- Misleading global winners: treatment improves average KPI but harms `value_seeker` segment.
- Exploration opportunities: some under-tested bundles outperform for minority segments.
- Tradeoffs: aggressive promotion can lift monetization proxy but reduce satisfaction_proxy.

## Constraints and Business Rules

- Parameter bounds must be respected.
- Forbidden combinations are rejected at arm-generation time.
- Max aggressive traffic: no more than 30% population on aggressive promotion.
- New users cannot receive high-challenge bundles above 20% traffic in v1.
- Risk guardrail: if expected satisfaction_proxy below threshold, arm is flagged.

## Realism Levels

### Level 1 - Minimal benchmark (v1 default)

- Four segments, modest treatment grid, simple delayed effect term.
- Fast simulation, high interpretability.

### Level 2 - Realistic benchmark

- Richer segment mixtures, additional interaction terms, stronger temporal carryover.
- Additional event types and heterogeneous noise.

### Level 3 - Extended benchmark

- Multiple domain templates, richer temporal dynamics, expanded behavioral pathways.
- Optional policy simulation and multi-objective optimization stress tests.

## Open Questions

- Which KPI floor constraints should be hard requirements in benchmark scoring?
- Which segment harms are unacceptable versus acceptable tradeoffs?
- How much delayed effect strength is needed before environment is sufficiently non-trivial?
- Should treatment allocation constraints vary by objective (retention vs engagement)?
