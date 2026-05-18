# Adaptive Experimentation Agent
## Proposed Architecture (Working Draft)

### Positioning
This architecture is intentionally flexible. It should evolve based on:
1. the final data structures and metrics we can realistically ground the system on,
2. the quality and granularity of those reference data,
3. early prototyping results,
4. technical constraints discovered during implementation.

Our goal is to define a strong default system design, not to lock the project too early into one rigid implementation choice.

The current direction is aligned with the project framing already developed in the deck: the core problem is not measuring experiments, but closing the loop from experiment results to next-best decisions in high-dimensional environments.

---

## 1. System Objective

Build a standardized agentic system that turns experiment data into:

- validated experiment insights,
- next-best experiment recommendations,
- optional adaptive policy updates over time.

### MVP philosophy
We start with:

**data -> evaluation -> recommendation**

before moving toward:

**data -> evaluation -> recommendation -> adaptive allocation**

This means the first version is **recommendation-first**, not full autonomous optimization.

---

## 2. Design Principles

### 2.1 Standardized, not bespoke
The system should work across domains with limited changes:
- gaming,
- product experimentation,
- marketing experimentation,
- pricing / offer testing,
- operational parameter tuning.

### 2.2 Modular, not monolithic
We do not want one opaque agent doing everything.
We want a general orchestrator coordinating reusable skills.

### 2.3 Auditable by design
LLMs should help generate, summarize, and propose.
Statistical evaluation and causal claims should remain explicit and reproducible.

### 2.4 Human-in-the-loop by default
The system should recommend and explain next actions before any future move toward autonomous execution.

### Use pre created middleware for that (Langchain)

### 2.5 Bandit-ready, RL-extendable
The architecture should support future adaptive allocation, but should not depend on RL from day one.

---

## 3. High-Level Architecture

### Layer 0 — Data Contracts
Defines the standard objects used across the system:
- `context`
- `action` / `treatment`
- `outcome`
- `constraints`
- `history`

This is the key standardization layer.

### Layer 1 — Data & Telemetry Backbone
Collects and structures:
- experiment logs,
- treatment / config tables,
- user or segment features,
- outcome metrics,
- event-level behavioral data,
- optional metadata on variants and design constraints.

### Layer 2 — Skill-Based Agent Layer
Core agent orchestration layer.
A general agent coordinates modular skills:
- retrieval,
- validation,
- evaluation,
- generation,
- recommendation.

### Layer 3 — Decision & Governance Layer
Produces:
- recommended next experiments,
- rationale,
- expected impact,
- uncertainty / confidence,
- approval-ready outputs.

---

## 4. Concrete Core Skills

### Skill 1 — Experiment Retrieval
**Purpose**
Retrieve relevant experiments, past variants, segments, and historical outcomes.

**Inputs**
- optimization objective,
- experiment history,
- filters / constraints.

**Outputs**
- relevant historical experiments,
- prior similar treatments,
- structured context package.

**Typical tools**
- SQL query tools,
- metadata retrieval,
- semantic retrieval over experiment summaries.

---

### Skill 2 — Validation & Diagnostics
**Purpose**
Check whether experiment data are usable and trustworthy.

**Checks**
- missing values,
- broken or inconsistent arms,
- sample size sufficiency,
- metric availability,
- obvious logging issues,
- treatment encoding integrity.

**Outputs**
- validation report,
- quality flags,
- go / caution / stop recommendation.

**Implementation (this repo)**  
LangGraph agent on branch `experimentation/validation-agent`: `src/agent/validation_agent.py`, `src/validation/`, exposed via `ValidationSkill` and `POST /validate/{experiment_id}`.  
→ See **[`docs/validation_agent.md`](validation_agent.md)** for flows, decision policy, configuration, and examples.

---

### Skill 3 — Causal Evaluation
**Purpose**
Estimate which experiments or variants appear to work, and for whom.

**Possible methods**
- standard A/B inference,
- difference in means,
- variance reduction,
- heterogeneous treatment effect analysis,
- uplift modeling,
- confidence intervals / uncertainty estimates.

**Outputs**
- estimated lift,
- segment-level effects,
- confidence / uncertainty,
- ranked candidate directions.

**Important**
This layer should remain mostly deterministic and statistically auditable.

---

### Skill 4 — Experiment Generation
**Purpose**
Generate the next candidate experiments or treatment bundles.

**Role of the LLM**
- summarize prior findings,
- reason over constraints,
- propose new parameter combinations,
- generate structured candidate variants,
- suggest hypotheses to test.

**Output format**
Strict structured schema, for example:
- candidate name,
- parameter changes,
- rationale,
- expected tradeoff,
- target segment,
- implementation notes.

---

### Skill 5 — Recommendation / Policy Selection
**Purpose**
Select what should be tested next.

**Possible scoring dimensions**
- expected impact,
- uncertainty,
- business priority,
- novelty,
- implementation complexity,
- strategic relevance.

**MVP approach**
Rule-based or scoring-based ranking.

**Future extension**
Contextual bandits for adaptive experiment allocation.

**Implementation (this repo)**  
LangGraph agent on branch `experimentation/recommendation-agent`: `src/agent/recommendation_agent.py`, `src/recommendation/`, `RecommendationSkill`, `POST /recommend/{experiment_id}`.  
→ See **[`docs/recommendation_agent.md`](recommendation_agent.md)** for scoring formula, graph nodes, and examples.

---

## 5. Recommended Execution Flow

### Step 1 — Objective definition
Examples:
- improve retention,
- increase engagement,
- optimize conversion,
- improve a segment-specific KPI,
- tune a high-dimensional parameter bundle.

### Step 2 — Retrieve relevant history
The system fetches:
- prior experiments,
- related variants,
- segment history,
- constraints and notes.

### Step 3 — Validate data quality
The system checks:
- data completeness,
- treatment integrity,
- metric reliability,
- sample sufficiency.

### Step 4 — Evaluate prior results
The system computes:
- effect estimates,
- uncertainty,
- segment heterogeneity,
- promising directions.

### Step 5 — Generate candidate next experiments
The LLM proposes:
- new variants,
- parameter bundles,
- experiment hypotheses,
- candidate traffic strategies.

### Step 6 — Rank next-best actions
The recommendation layer scores and orders the best next experiments.

### Step 7 — Human review
An analyst / PM / decision-maker approves or edits the final recommendation.

### Step 8 — Log back into memory
Results and decisions are stored for future retrieval and learning.

---

## 6. Data Model (for now)

### 6.1 Experiments
Fields:
- `experiment_id`
- `objective`
- `start_date`
- `end_date`
- `status`
- `traffic_split`
- `owner`
- `notes`

### 6.2 Arms / Variants
Fields:
- `experiment_id`
- `arm_id`
- `treatment_description`
- `structured_parameters_json`
- `treatment_type`
- `constraints_tag`

### 6.3 Observations
Fields:
- `entity_id` (user_id, segment_id, cohort_id)
- `experiment_id`
- `arm_id`
- `timestamp`
- `context_features_json`
- `outcomes_json`
- `exposure_flag`

### 6.4 Metrics Summary
Fields:
- `experiment_id`
- `arm_id`
- `sample_size`
- `conversion`
- `retention`
- `engagement`
- `revenue_proxy`
- `variance`
- `confidence_interval`

### 6.5 Experiment Memory
Fields:
- `experiment_id`
- `summary_text`
- `lessons_learned`
- `winning_patterns`
- `failed_patterns`
- `analyst_notes`

---

## 7. Technical Stack

## 7.1 Ideal Stack

### Orchestration
- **LangGraph** for agent workflow orchestration

Why:
- stateful graph-based execution,
- explicit control over flow,
- easier debugging than open-ended agent loops,
- well-suited for composable skills.

### Backend / API
- **FastAPI**

Why:
- lightweight,
- production-friendly,
- easy integration with Python analytics stack.

### Data Processing
- **Python**
- **pandas** or **polars**
- **SQLAlchemy** for database connectors

### Statistical / Causal Layer
- **statsmodels**
- **scikit-learn**
- to explore: **econml** or **causalml**

### Metadata Store
- **PostgreSQL**

### Retrieval / Memory
- **PostgreSQL + pgvector**
- alternative lightweight option: **Chroma**

### Frontend / Demo UI
- **Streamlit** for fast MVP
- optional later: **React** frontend
- Copilotkit

### Data Processing
- Pydsntic
- 2 agents (2nd can be LLM call): 1 for heavy work, 1 for structured output -> better accuracy


### Observability / Tracing
- **LangSmith**
- or custom structured logging

---

## 7.2 Alternatives to Consider

### Agent orchestration alternatives
- **CrewAI**
- **AutoGen**
- **Haystack Agents**
- **custom deterministic pipeline without agent framework**

Benchmark consideration:
If we want control and enterprise clarity, LangGraph is likely the strongest default.
If we want lighter prototyping, a custom orchestrator may be enough for v1.

### Warehouse / storage alternatives
- **Databricks**
- **Snowflake**
- **BigQuery**
- **DuckDB + Parquet** for local prototype

### Frontend alternatives
- **Gradio**
- **CopilotKit** - to research - middleware: AGUI currently Industry Standard
- **plain notebook + dashboard screenshots** for earliest version

### Bandit layer alternatives
- **MABWiser**
- **Vowpal Wabbit**
- **custom LinUCB / Thompson Sampling implementation**

### Reco:
Make agents MCP compatible - for a central MCP based (SOTA in the industry like AGUI)
Start with pre built agent with skills, only byuild custom agent if pre ones can't get accuracy/results
Deepagent to try: setup different agents and test them - answer: is it too much for one agent?  need additional tool/skills...?
Agent to exectue against thos: 1 for retrieval (SQL access), separate agent for unstructured data retrieval. 
Find right level of constraints and access of tools for each agent - general reco not more than 10 tools (break down in multi sub agents)
**Progressive disclosure**: entire repo of tools/skills but we don't want all of it at once as context. Look up details so it retrieve only whats needed in context -> memory engineering / Multi agent can solve that to offload context (e.g., middleware within langchain automaticly truggers summarization)
Langchain sanboxing (e.g., Daytona)

Add visual diagrams - e.g different langgraph nodes, etc. before starting coding

Development plan: file structure, based agent function to be called... and building on these standardized things. -> break that up into different features request (e.g., submitting issue requests on github)
Make sure to build observability as soon as possible (LangSmith)


---

## 8. Role of the LLM

### Good uses
- experiment summarization,
- structured hypothesis generation,
- treatment proposal generation,
- rationale generation,
- constrained SQL drafting,
- explanation for analysts.

### Bad uses
- replacing statistical tests,
- making causal claims directly,
- validating data logic,
- silently deciding production rollouts.

### Principle
The LLM should be a **proposal and orchestration layer**, not the source of truth for evaluation.

---

## 9. Optimization Strategy

### MVP
- deterministic evaluation,
- recommendation ranking,
- static next-best experiment suggestions.

### Phase 2
- contextual bandits for adaptive allocation,
- exploration vs exploitation,
- policy selection under uncertainty.

### Phase 3
- offline RL or model-based RL,
- sequential decision problems,
- delayed rewards,
- richer environments / simulations.

### Choice for now
No full RL in v1.
We would keep RL as a future extension.

---

## 10. Data Strategy

### Current direction
Our primary direction is to build a **realistic synthetic data environment** grounded in:
- real industry metrics,
- realistic experiment schemas,
- real or industry-inspired parameter/configuration tables,
- plausible relationships between treatments, contexts, and outcomes.

The goal is not to produce arbitrary synthetic data, but to generate a controlled environment that reflects the structure and constraints of real experimentation systems closely enough to support credible prototyping and evaluation.

### Why this direction
This gives us:
- more control over treatment space design,
- the ability to test high-dimensional settings,
- flexibility for simulation and counterfactual exploration,
- a practical path when direct access to proprietary production data is limited.

### Three possible modes

#### Option A — Realistic synthetic environment grounded in real industry structures
Preferred path for the project.
Use real metrics definitions, realistic parameter tables, and industry-inspired schemas to generate credible synthetic observations and experiments.

#### Option B — Semi-synthetic extension if partial real data become available (calls to come)
If we get access to partial experiment logs, metrics tables, or benchmarked aggregates, we can anchor the synthetic generator even more tightly to real distributions.

#### Option C — Fully real experiment data
Best case if available later, but not required for the initial system architecture.

---

## 11. MVP Scope

### Included in MVP
- ingest experiment history,
- validate experiment data,
- compute experiment outcomes,
- summarize prior results,
- generate next experiment candidates,
- rank next-best actions,
- store experiment memory.

### Excluded from MVP
- direct autonomous production deployment,
- full RL loop,
- complex simulation engine,
- CV / gameplay perception layer,
- heavy multi-agent architecture.

---

## 12. Risks / Open Questions

### Data risks
- synthetic data may fail to capture important real-world dependencies,
- weak or unrealistic treatment encoding,
- limited grounding on real distributions,
- noisy outcome design assumptions.

### Modeling risks
- weak causal identifiability if the synthetic generator is poorly designed,
- LLM over-generation,
- recommendation quality depends on how realistic the synthetic history is.

### Product / infra risks
- integration effort,
- governance requirements,
- stakeholder trust in automated recommendations.

---

## 13. Final output objective

We are **not** proposing a fully autonomous optimization engine from day one.

We are proposing a **standardized adaptive experimentation agent** that:
- ingests experiment data,
- evaluates outcomes rigorously,
- generates next-best experiment ideas,
- recommends what to test next,
- and prepares the system for future adaptive optimization.

This is a pragmatic path from:
**manual experimentation -> standardized recommendation -> adaptive decision systems**

This is a modular, skill-based experimentation agent that closes the loop from experiment results to next-best decisions, without requiring a heavyweight specialized optimization stack and manual work.
